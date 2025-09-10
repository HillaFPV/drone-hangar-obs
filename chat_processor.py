import asyncio
import json
import logging
import time
import rule_engine
from obswebsocket import obsws, requests
import socket

font_path = {
    'DESKTOP-SFA8JUV': "C:/Users/Desktop/Desktop/Drone Hangar 3.0",
    'Origin': "C:/Users/Chris/Desktop/The CREW AI/fonts"
}.get(socket.gethostname())

from models.chat_models import ChatMessage, BatteryMessage, TextMessage

# All the OBSWS protocol stuff you need is here:
# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

logging.basicConfig(filename="../logs/chat-processor.log",
                    filemode='a',
                    format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger('chat-processor')
logging.info("Starting chat processor")

colors = {'yellow': 4278321147,
          'green': 4278255445,
          'orange': 4279856639,
          'dark_green': 4278233600}

THERMOMETER_STEPS = 50

class ChatProcessor:
    def __init__(self):
        # Pre-populate this with people you don't want to be able to ring the door chime upon chatting for the first time
        self.chatters = {"HillaFPV": 0,
                         "Dank Cloudz FPV": 0,
                         "Allen Applewhite (Creeper FPV)": 0,
                         "That Guy Phly": 0,
                         "WallBanger": 0,
                         "RidiFPV": 0
                         }
        self.chat_total_count = 0
        self.chat_pole_fill_amount = 0

    def reset(self):
        self.chatters = {"HillaFPV": 0,
                         "Dank Cloudz FPV": 0,
                         "Allen Applewhite (Creeper FPV)": 0,
                         "That Guy Phly": 0,
                         "WallBanger": 0,
                         "RidiFPV": 0
                         }
        self.chat_total_count = 0
        self.chat_pole_fill_amount = 0

    def reset_pole(self):
        self.chat_pole_fill_amount = 0
        update_thermometer(self.chat_pole_fill_amount)

    def set_battery(self, battery_message: BatteryMessage):
        volts_string = str(int(battery_message.volts * 100))
        battery_percentage = int(volts_string) - 320

        if 80 < battery_percentage <= 100:
            battery_chunk = 8
        elif 60 < battery_percentage <= 80:
            battery_chunk = 7
        elif 50 < battery_percentage <= 60:
            battery_chunk = 6
        elif 40 < battery_percentage <= 50:
            battery_chunk = 5
        elif 30 < battery_percentage <= 40:
            battery_chunk = 4
        elif 20 < battery_percentage <= 30:
            battery_chunk = 3
        elif 0 <= battery_percentage <= 20:
            battery_chunk = 2
        else:
            battery_chunk = 1

        print(battery_percentage, battery_chunk)
        ws.call(requests.SetInputSettings(inputName=f"OSD-Battery-Icon", inputSettings={
            "file": f"{font_path}/Battery-{battery_chunk}.png"
        }))
        for i, char in enumerate(volts_string):
            ws.call(requests.SetInputSettings(inputName=f"OSD-Volts-{i+1}", inputSettings={
                "file": f"{font_path}/{char}.png"
            }))


    def set_text(self, text_message: TextMessage):
        for i, char in enumerate(text_message.text.center(20)):
            if char == " ":
                char = "Space"
            if char == "*":
                char = "Asterisk"
            ws.call(requests.SetInputSettings(inputName=f"OSD-Text-Char-{i+1}", inputSettings={
                "file": f"{font_path}/{char}.png"
            }))

    def set_clock(self, text_message: TextMessage):
        for i, char in enumerate(text_message.text):
            if char == " ":
                char = "Space"
            if char == "*":
                char = "Asterisk"
            if char == ":":
                char = "Colon"
            ws.call(requests.SetInputSettings(inputName=f"OSD-Fly-Time-{i+1}", inputSettings={
                "file": f"{font_path}/{char}.png"
            }))


    async def process_chat(self, chat_message: ChatMessage):
        self.chat_total_count += 1
        self.chat_pole_fill_amount += 1
        if self.chat_pole_fill_amount <= THERMOMETER_STEPS:
            update_thermometer(self.chat_pole_fill_amount)
        else:
            self.chat_pole_fill_amount = 0
            send_websocket_message("chat overflow")

        change_source_text("Chat-Thermometer-Text", self.chat_total_count, colors['yellow'], colors['orange'])

        context = rule_engine.Context(type_resolver=rule_engine.type_resolver_from_dict({
            'author': {
                'name': rule_engine.DataType.STRING,
                'imageUrl': rule_engine.DataType.STRING,
                'isVerified': rule_engine.DataType.BOOLEAN,
                'isChatOwner': rule_engine.DataType.BOOLEAN,
                'isChatSponsor': rule_engine.DataType.BOOLEAN,
                'isChatModerator': rule_engine.DataType.BOOLEAN
            },
            'type': rule_engine.DataType.STRING,
            'message': rule_engine.DataType.STRING,
            'amountValue': rule_engine.DataType.FLOAT
        }))

        flat_message = chat_message.model_dump()
        logger.info(json.dumps(flat_message))

        # Chat Message Rules
        dank_dunk_tank_rule = rule_engine.Rule("""
            (author.name == "Dank Cloudz FPV" and "balls" in message.as_lower) or
            (author.name == "HillaFPV" and "Wake up, dank!" in message)
            """, context=context)

        superchat_rule = rule_engine.Rule("""
            (type == "superChat" and amountValue < 4.20) or
            (author.name == "HillaFPV" and "!!superchat" in message)
            """, context=context)

        dab_superchat_rule = rule_engine.Rule("""
            (type == "superChat" and amountValue >= 4.20 and amountValue < 10.00 ) or
            (author.name == "HillaFPV" and "!!dabsuperchat" in message)
            """, context=context)

        big_superchat_rule = rule_engine.Rule("""
            (type == "superChat" and amountValue > 10.00) or
            (author.name == "HillaFPV" and "!!bigsuperchat" in message)
            """, context=context)

        squirrel_mother_rule = rule_engine.Rule("""
            author.name == "Juliana Anderson"
            """, context=context)

        # New Chatter Announcement
        if chat_message.author.name not in self.chatters:
            self.chatters.update({chat_message.author.name: 0})

            # Change the text on the "Chat Enter Name" on the Tet GDI+ source
            change_source_text("Chat Enter Name",
                               f"        {chat_message.author.name}    has    joined!")

            send_websocket_message("first time chatter")

        self.chatters.update({chat_message.author.name: self.chatters[chat_message.author.name] + 1})

        # Put rules evaluations here:
        if superchat_rule.matches(flat_message):
            change_source_text("Super Chat Scrolling Text",
                               f" " * 40 + f"{chat_message.amountString}      SUPER CHAT FROM {chat_message.author.name}!!!" + " " * 30)
            launchpoint_scene_name = ws.call(requests.GetCurrentProgramScene()).getSceneName()

            ws.call(requests.SetCurrentProgramScene(
                sceneName="-------->SUPER CHAT Sv Ver."
            ))

            await asyncio.sleep(18)

            ws.call(requests.SetCurrentProgramScene(
                sceneName=launchpoint_scene_name
            ))

        if dab_superchat_rule.matches(flat_message):
            change_source_text("Super Chat Scrolling Text",
                               f" " * 40 + f"{chat_message.amountString}      SUPER CHAT FROM {chat_message.author.name}!!!" + " " * 30)

            launchpoint_scene_name = ws.call(requests.GetCurrentProgramScene()).getSceneName()

            ws.call(requests.SetCurrentProgramScene(
                sceneName="-------->SUPER CHAT Sv Ver."
            ))

            await asyncio.sleep(18)

            ws.call(requests.SetCurrentProgramScene(
                sceneName="---->DH Lougne 2025"
            ))

            await asyncio.sleep(4)

            send_websocket_message("shelby glide 3")

            await asyncio.sleep(12)

            ws.call(requests.SetCurrentProgramScene(
                sceneName=launchpoint_scene_name
            ))

        if big_superchat_rule.matches(flat_message):
            change_source_text("Super Chat Scrolling Text",
                               f" " * 40 + f"{chat_message.amountString}      SUPER CHAT FROM {chat_message.author.name}!!!" + " " * 30)

            launchpoint_scene_name = ws.call(requests.GetCurrentProgramScene()).getSceneName()

            ws.call(requests.SetCurrentProgramScene(
                sceneName="-------->SUPER CHAT Sv Ver."
            ))

            await asyncio.sleep(18)

            ws.call(requests.SetCurrentProgramScene(
                sceneName="---->DH Lougne 2025"
            ))

            await asyncio.sleep(1)
            send_websocket_message("shelby glide 1")
            await asyncio.sleep(3)
            send_websocket_message("shelby glide 2")
            await asyncio.sleep(20)
            send_websocket_message("shelby glide 3")

            await asyncio.sleep(20)

            ws.call(requests.SetCurrentProgramScene(
                sceneName=launchpoint_scene_name
            ))

        if dank_dunk_tank_rule.matches(flat_message):
            send_websocket_message("dank dunk tank")


while True:
    try:
        host = "localhost"
        port = 4455
        password = ""
        ws = obsws(host, port, password)
        ws.connect()
        break
    except Exception as e:
        logger.info("Unable to connect to OBS: ", str(e))
        time.sleep(2)


def get_scene_item(scene_name, scene_item_name):
    scene_items = ws.call(requests.GetSceneItemList(sceneName=scene_name)).datain['sceneItems']
    for scene_item in scene_items:
        if scene_item['sourceName'] == scene_item_name:
            return scene_item


def update_thermometer(percentage):
    scene_item = get_scene_item("Chat Thermometer", "Chat-Thermometer-Full")
    scene_item_id = scene_item['sceneItemId']
    scale_y = scene_item['sceneItemTransform']['scaleY']

    if percentage >= 50:
        transform = {'cropTop': 0, 'positionY': 0}

        ws.call(requests.SetSceneItemTransform(sceneName="Chat Thermometer",
                                               sceneItemId=scene_item_id,
                                               sceneItemTransform=transform))
    else:

        baseline = 896  # Specific to this PNG asset
        increment = 600 / THERMOMETER_STEPS # 6px = 1% for this PNG asset

        top = baseline - (percentage * increment)
        crop = top / scale_y

        transform = {'cropTop': crop, 'positionY': top}

        ws.call(requests.SetSceneItemTransform(sceneName="Chat Thermometer",
                                               sceneItemId=scene_item_id,
                                               sceneItemTransform=transform))


def source_restart_media(source):
    """
    source: Media Source name to press restart on ,eg: "Shelby Glide 2"
    """
    ws.call(requests.TriggerMediaInputAction(
        inputName=source,
        mediaAction="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    ))


def send_websocket_message(message):
    ws.call(requests.CallVendorRequest(
        vendorName="AdvancedSceneSwitcher",
        requestType="AdvancedSceneSwitcherMessage",
        requestData={
            "message": message
        }
    ))


def change_source_text(source, message, color=None, gradient_color=None):
    # Change the text on a Text GDI+ source

    input_settings = {"text": str(message)}
    if color:
        input_settings["color"] = color
    if gradient_color:
        input_settings["gradient_color"] = gradient_color

    ws.call(requests.SetInputSettings(
        inputName=source,
        inputSettings=input_settings
    ))

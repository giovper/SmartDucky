import time
import digitalio
from board import *
import board
import json
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
# change for non US keyboards
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayout(keyboard)
mouse = Mouse(usb_hid.devices)
conn = None

# Mappa per i tasti modificatori booleani
MODIFIER_MAP = {
    'true': True,
    'false': False,
    'True': True,
    'False': False
}

def onRequestRecived(mType, mValue):
    print("Command about to execute! - " + str(mType) + " - " + str(mValue))
    if (mType == "code"):
        for line in mValue.splitlines():
            runLine(line)
    elif (mType == "live"):
        runLine(mValue)
    elif (mType == "interrupt"):
        pass
    elif (mType == "control"):
        playControlKey(mValue)
    
    print("Command executed! - " + str(mType) + " - " + str(mValue))

def playControlKey(data):
    parts = data.split(" ")
    controltype = parts[0]
    
    if controltype == "key":
        # Format from web: "key [keyname] [ctrl_bool] [shift_bool] [alt_bool] [meta_bool]"
        if len(parts) >= 2:
            key_name = parts[1]
            
            # Parse modifier flags (default to False if not provided)
            ctrl_pressed = False
            shift_pressed = False
            alt_pressed = False
            meta_pressed = False
            
            if len(parts) >= 3:
                ctrl_pressed = parts[2].lower() == 'true'
            if len(parts) >= 4:
                shift_pressed = parts[3].lower() == 'true'
            if len(parts) >= 5:
                alt_pressed = parts[4].lower() == 'true'
            if len(parts) >= 6:
                meta_pressed = parts[5].lower() == 'true'
            
            # Build list of keys to press
            keys_to_press = []
            
            # Add modifiers first
            if ctrl_pressed:
                keys_to_press.append(Keycode.CONTROL)
            if shift_pressed:
                keys_to_press.append(Keycode.SHIFT)
            if alt_pressed:
                keys_to_press.append(Keycode.ALT)
            if meta_pressed:
                keys_to_press.append(Keycode.GUI)  # Windows/Cmd key
            
            # Map special key names to Keycode
            key_mapping = {
                'Enter': Keycode.ENTER,
                'Return': Keycode.ENTER,
                'Backspace': Keycode.BACKSPACE,
                'Delete': Keycode.DELETE,
                'Tab': Keycode.TAB,
                'Escape': Keycode.ESCAPE,
                'Space': Keycode.SPACE,
                'ArrowUp': Keycode.UP_ARROW,
                'ArrowDown': Keycode.DOWN_ARROW,
                'ArrowLeft': Keycode.LEFT_ARROW,
                'ArrowRight': Keycode.RIGHT_ARROW,
                'Home': Keycode.HOME,
                'End': Keycode.END,
                'PageUp': Keycode.PAGE_UP,
                'PageDown': Keycode.PAGE_DOWN,
                'Insert': Keycode.INSERT,
                'CapsLock': Keycode.CAPS_LOCK,
                'NumLock': Keycode.KEYPAD_NUMLOCK,
                'ScrollLock': Keycode.SCROLL_LOCK,
                'PrintScreen': Keycode.PRINT_SCREEN,
                'Pause': Keycode.PAUSE,
                'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3, 'F4': Keycode.F4,
                'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7, 'F8': Keycode.F8,
                'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11, 'F12': Keycode.F12,
            }
            
            # Get the main key
            if key_name in key_mapping:
                main_key = key_mapping[key_name]
            elif len(key_name) == 1:
                # Single character - convert to uppercase for Keycode attribute
                key_attr = key_name.upper()
                if hasattr(Keycode, key_attr):
                    main_key = getattr(Keycode, key_attr)
                else:
                    print(f"Key '{key_name}' not found in Keycode")
                    return
            else:
                # Try direct Keycode attribute lookup
                key_attr = key_name.upper()
                if hasattr(Keycode, key_attr):
                    main_key = getattr(Keycode, key_attr)
                else:
                    print(f"Key '{key_name}' not recognized")
                    return
            
            # Add main key to the list
            keys_to_press.append(main_key)
            
            # Press all keys
            if keys_to_press:
                print(f"Pressing keys: {[str(k) for k in keys_to_press]}")
                keyboard.press(*keys_to_press)
                delay(50)  # Short delay
                keyboard.release_all()
        
    elif controltype == "mouse_move":
        # Format: "mouse_move deltaX deltaY"
        try:
            delta_x = int(parts[1])
            delta_y = int(parts[2])
            mouse.move(x=delta_x, y=delta_y)
            print(f"Mouse moved by: {delta_x}, {delta_y}")
        except (IndexError, ValueError):
            print("Invalid mouse move command.")
    
    elif controltype == "mouse_pos":
        # Format: "mouse_pos x y" (legacy absolute positioning)
        try:
            x = int(parts[1])
            y = int(parts[2])
            # Note: Most HID mice don't support absolute positioning
            # This is here for backwards compatibility but may not work as expected
            mouse.move(x=x, y=y)
            print(f"Mouse moved to: {x}, {y}")
        except (IndexError, ValueError):
            print("Invalid mouse position command.")
    
    elif controltype == "mouse_button":
        # Format: "mouse_button l/r/m/o"
        try:
            button = parts[1].lower()
            if button == "l":
                mouse.press(Mouse.LEFT_BUTTON)
                delay(50)
                mouse.release(Mouse.LEFT_BUTTON)
                print("Left mouse button clicked")
            elif button == "r":
                mouse.press(Mouse.RIGHT_BUTTON)
                delay(50)
                mouse.release(Mouse.RIGHT_BUTTON)
                print("Right mouse button clicked")
            elif button == "m":
                mouse.press(Mouse.MIDDLE_BUTTON)
                delay(50)
                mouse.release(Mouse.MIDDLE_BUTTON)
                print("Middle mouse button clicked")
            else:
                print(f"Unknown mouse button: {button}")
        except IndexError:
            print("Missing mouse button parameter.")

def releaseKeyboard():
    keyboard.release_all()
    
def typeString(line):
    layout.write(line)

def delay(ms):
    time.sleep(ms/1000.0)

def moveX(xVal):
    mouse.move(x=xVal)
    
def moveY(yVal):
    mouse.move(y=yVal)

def moveMouse(xVal, yVal):
    mouse.move(x=xVal, y=yVal)

def sendBack(message):
    response = json.dumps({"return": message})
    http_response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(response)}\r\n"
        "\r\n"
        + response
    )
    conn.send(http_response.encode("utf-8"))

global_env = {
    "conn": conn,
    "sendBack": sendBack,
    "delay": delay,
    "typeString": typeString,
    "releaseKeyboard": releaseKeyboard,
    "moveX": moveX,
    "moveY": moveY,
    "moveMouse": moveMouse,
    "keyboard": keyboard,
    "mouse": mouse,
    "Keycode": Keycode,
    "Mouse": Mouse
}

local_env = {}

def runLine(code):
    exec(code, global_env, local_env)
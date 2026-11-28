import os, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOICE = "am_michael"
LEAD, TAIL = 0.6, 0.8

EP1 = {
 "01_hook": "You press this button. A few seconds later, you're looking at a login screen. So what actually happened in between?",
 "02_power": "First, the power supply ramps up its voltage rails: twelve volts, five volts, and three point three volts. Only when they are stable does it raise Power Good, and the CPU is finally let out of reset.",
 "03_vector": "The CPU wakes up knowing exactly one thing: the hard-wired address of its first instruction. On x86, that's hex, seven F's and a zero. This is the reset vector.",
 "04_post": "That jump lands in the firmware, BIOS or UEFI, which runs the Power-On Self-Test, and trains your RAM.",
 "05_bootdev": "Next, it hunts for something bootable. Legacy BIOS checks the first sector for the magic bytes, five five, A A. UEFI looks for a bootloader file instead.",
 "06_loader": "The bootloader, such as GRUB, or Windows Boot Manager, copies the operating system kernel into RAM, and hands over control.",
 "07_kernel": "The kernel takes control of the hardware, loads drivers, mounts your file system, and starts the very first process.",
 "08_recap": "Power. Reset. Firmware. Bootloader. Kernel. Login. Six handoffs, all in a few seconds.",
 "09_end": "Next episode: how does a microcontroller actually run your code? Subscribe so you don't miss it.",
}
SHORT = {
 "s1": "Your CPU wakes up knowing just one thing. Here's what happens the instant you press power.",
 "s2": "Step one: wait for stable power. Voltages ring and settle. Only then does Power Good go high, and reset lets go.",
 "s3": "Step two: the first instruction. It lives at a hard-wired address: hex, seven F's and a zero. It's called the reset vector.",
 "s4": "Then five more handoffs, all in a few seconds, before you ever see a login screen.",
 "s5": "The full breakdown of all six steps is in the full video.",
}

EP2 = {
 "01_hook": "You write a few lines of C. Seconds later, a light blinks. So how does text on a screen become electricity in a wire?",
 "02_compile": "Step one: compile. The compiler translates your C into machine instructions. Load an address, load a value, flip a bit, store it back. And each instruction is just a number.",
 "03_flash": "Step two: flash. A programmer like the ST-Link writes those numbers into the chip's flash memory, which keeps them even with the power off.",
 "04_vector": "Step three: reset. The core reads two words from the start of flash: the starting stack pointer, and the address of the reset handler. Startup code copies data into RAM, zeroes the rest, sets up the clock, and finally calls main.",
 "05_cycle": "Step four: the loop at the heart of every CPU. Fetch the instruction at the program counter. Decode it. Execute it. Then move on to the next one. Forever.",
 "06_mmio": "Here's the secret. Address hex, four eight, zero zero, zero zero, one four, isn't memory at all. It's a register wired straight to the GPIO pins. Writing a one to bit five drives pin P A five high, and the LED lights up.",
 "07_clock": "A crystal oscillator sets the pace. At seventy-two megahertz, this little loop could run millions of times every second. That's why we need a delay.",
 "08_recap": "Compile. Flash. Reset. Fetch, decode, execute. And a write to the right address. That's how every program you'll ever run turns into something real.",
 "09_end": "Next episode: what really happens when you press a key? Subscribe so you don't miss it.",
}
SHORT2 = {
 "s1": "This LED is controlled by one single address. Here's how your code flips a real pin.",
 "s2": "Your C code compiles into machine instructions, and every instruction is just a number, stored in flash.",
 "s3": "The CPU fetches each one, decodes it, and executes it, up to seventy-two million times a second.",
 "s4": "And here's the secret. Address hex, four eight, zero zero, zero zero, one four, isn't memory at all. It's wired straight to the pin.",
 "s5": "The full journey from code to light is in the full video.",
}

EP3 = {
 "01_hook": "You press a key, and a letter appears, in a few milliseconds. But here's the twist: your keyboard never actually sends the letter.",
 "02_matrix": "Step one: the key matrix. Under the keys is a grid of wires, in rows and columns. The keyboard's microcontroller scans it, driving one column at a time and reading the rows, hundreds of times a second. When a key is pressed, it connects a row to a column, and the controller knows exactly where it is.",
 "03_debounce": "Step two: debounce. Metal contacts bounce, flickering on and off for a few milliseconds. The firmware waits for the signal to settle, so one press counts as exactly one press.",
 "04_report": "Step three: the HID report. The keyboard doesn't send the letter A. It sends a code that means, the key in this position: usage four. That code is packed into an eight-byte report, with room for six keys at once, plus a byte for Shift, Control and Alt.",
 "05_poll": "Step four: USB polling. A USB keyboard can't interrupt the computer on its own. Instead, the host asks it, every few milliseconds: anything new? Usually the answer is no. But this time, the keyboard answers with its report.",
 "06_driver": "Step five. The USB controller drops the report into memory, and raises an interrupt on the CPU. The HID driver picks it up, and applies your keyboard layout. The same code, four, becomes a lowercase a on a QWERTY keyboard, but a q on a French AZERTY keyboard.",
 "07_screen": "Step six. The operating system sends a key event to whichever window has focus. The app adds the letter, the font engine draws its glyph as pixels, and on the next screen refresh, there it is.",
 "08_recap": "Scan. Debounce. Report. Poll. Interrupt. Layout. Draw. All of it, in the time it takes to blink.",
 "09_end": "Next episode: how does USB know what you plugged in? Subscribe so you don't miss it.",
}
SHORT3 = {
 "s1": "Your keyboard never sends the letter A. So what does it actually send?",
 "s2": "First, it scans a grid of wires, one column at a time, hundreds of times a second.",
 "s3": "Then it sends a number. Hex zero four. It just means: the key in this position.",
 "s4": "Your operating system decides what that means. On QWERTY, it's a. On a French AZERTY keyboard, it's q.",
 "s5": "The full journey from fingertip to pixel is in the full video.",
}

EP4 = {
 "01_hook": "You plug something in. A second later, it just works. But at first, your computer had no idea what that thing was. So how does it find out?",
 "02_detect": "Step one: detect. The device has a tiny pull-up resistor on one of its data lines. When you plug it in, that line's voltage rises, and the host knows something is attached. Which line goes high even tells the host how fast the device can talk.",
 "03_reset": "Step two: reset. The host resets the new device by pulling both data lines low. After a reset, every new device answers at the same default address: zero. That's why devices are set up one at a time.",
 "04_describe": "Step three: the host asks, who are you? The device answers with its device descriptor. Eighteen bytes that say which company made it, which product it is, and how big its packets can be. The vendor I D and product I D together identify that exact model.",
 "05_address": "Step four: set address. The host gives the device its own unique address, a number from one to one hundred and twenty seven. Address zero is now free for the next device you plug in.",
 "06_class": "Step five: configuration. The host reads the device's interfaces, its endpoints, and its class code. Class three means human interface device, like a keyboard or mouse. Class eight means mass storage, like a flash drive. Audio and video have their own classes too.",
 "07_driver": "Step six: the driver. The operating system matches the vendor and product I D, or the class code, to a driver, and loads it. It sends set configuration, and your device is ready to use. Ding.",
 "08_recap": "Detect. Reset. Describe. Address. Configure. Load a driver. A whole conversation, in a fraction of a second.",
 "09_end": "Next episode: I squared C, S P I, and UART. How do chips actually talk to each other? Subscribe so you don't miss it.",
}
SHORT4 = {
 "s1": "Your computer has no idea what you just plugged in. So it has to ask.",
 "s2": "Every new device starts at address zero. The host asks it: who are you?",
 "s3": "It answers with a name tag: a vendor I D for who made it, a product I D for which model, and a class code for what it is.",
 "s4": "The class code picks the driver. Three is a keyboard or mouse. Eight is a flash drive. Load the driver, and it just works.",
 "s5": "The whole USB handshake is in the full video.",
}

EP5 = {
 "01_hook": "Your microcontroller is surrounded by other chips: sensors, displays, memory, radios. They all talk through just a few wires, using one of three languages: you-art, S P I, and I squared C.",
 "02_uart": "First, you-art. It's the simplest. Two wires, crossed over, so my transmit goes to your receive. There's no clock wire at all, so both sides must agree on the speed in advance. A common choice is one hundred fifteen thousand, two hundred bits per second.",
 "03_uart_frame": "To send the letter A, the line drops low for a start bit. Then come eight data bits, least significant bit first. Then the line goes high again for a stop bit. The receiver times every bit using the speed you both agreed on.",
 "04_spi": "Next, S P I. It adds a clock wire, so the controller sets the pace. Data goes out on one wire, and comes back on another, at the same time. And every chip gets its own chip select line, so the controller can pick who it's talking to.",
 "05_spi_wave": "Pull chip select low, and the clock starts ticking. On every tick, one bit goes out, and one bit comes back. And it can run at tens of megahertz. That's why displays and SD cards love S P I.",
 "06_i2c": "Finally, I squared C. Just two wires, shared by every chip on the bus: data and clock, each held high by a pull-up resistor. Every chip has its own address, so dozens of them can share the same two wires.",
 "07_i2c_frame": "A transaction starts with a start condition. Then comes the address of the chip you want, plus a read or write bit. Only that chip answers, with an acknowledge. Then the data flows, and a stop condition ends it.",
 "08_compare": "So which one wins? None of them. Use you-art for simple point to point links. Use S P I when you need speed. And use I squared C when you want lots of chips on just two wires.",
 "09_end": "Next episode: how does P W M dim an LED? Subscribe so you don't miss it.",
}
SHORT5 = {
 "s1": "Chips talk to each other in three languages. Here's each one, fast.",
 "s2": "You-art has no clock. Just two wires, and both sides agree on the speed in advance. Perfect for GPS modules and debug consoles.",
 "s3": "S P I has its own clock, and it's fast, tens of megahertz. But every chip needs its own select wire.",
 "s4": "I squared C uses just two wires for many chips. You call a chip by its address, and only that chip answers.",
 "s5": "Which one should you use? Watch the full video.",
}

EP6 = {
 "01_hook": "A microcontroller pin can only be fully on, or fully off. So how does it make an LED glow at half brightness? Or a motor spin at half speed?",
 "02_digital": "Here's the problem. A digital pin has exactly two settings: three point three volts, or zero. There is no setting for half-way.",
 "03_blink": "So instead, it cheats. It blinks. Once a second, you can see the flicker. Eight times a second, it's still annoying. But speed it up to a thousand times a second, and your eye just averages it into a steady glow.",
 "04_duty": "The secret is the duty cycle: the share of each cycle the pin spends switched on. On for ten percent of the time, the LED looks dim. Fifty percent, medium. Ninety percent, bright. The average voltage follows the duty cycle.",
 "05_timer": "And the CPU doesn't do this in code. A hardware timer counts up, over and over, and resets. While the count is below a compare value, the pin is high. Once it passes it, the pin goes low. Move the compare value, and the brightness changes.",
 "06_code": "In code, you set the timer up once. Divide the seventy two megahertz clock down to one megahertz, and count to a thousand, for a one kilohertz signal. Then, writing two hundred and fifty to the compare register gives you twenty five percent. The hardware does the rest, while your code does something else.",
 "07_uses": "And it's not just LEDs. The same trick controls motor speed, sets the angle of a hobby servo with pulses between one and two milliseconds, makes simple sounds, and runs the switching power supply charging your phone.",
 "08_recap": "A pin can't do half-way. So it switches on and off, fast. The duty cycle sets the average, and a hardware timer does it all for free.",
 "09_end": "Next episode: interrupts. How does a CPU get tapped on the shoulder? Subscribe so you don't miss it.",
}
SHORT6 = {
 "s1": "A microcontroller pin can't do half. It's either on, or off. So how does an LED dim?",
 "s2": "It blinks. Fast. A thousand times a second, and your eye averages it into a steady glow.",
 "s3": "The more time it spends on, the brighter it looks. That's called the duty cycle.",
 "s4": "And a hardware timer does it for free. Count up, compare, flip the pin. One register sets the brightness.",
 "s5": "How P W M really works is in the full video.",
}

def build(mod, lines, outdir, final, speed):
    voice = getattr(mod, "VOICE", VOICE)
    speed = getattr(mod, "SPEED", speed)
    lang = getattr(mod, "LANG", "en-us")
    print("voice", voice, "speed", speed, "lang", lang, flush=True)
    os.makedirs(outdir, exist_ok=True)
    tts = os.environ.get("TTS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".tts"))
    k = Kokoro(os.path.join(tts, "kokoro.onnx"), os.path.join(tts, "voices.bin"))
    scenes, track, sr = [], [], 24000
    for name, fn, dur in mod.SCENES:
        a, sr = k.create(lines[name], voice=voice, speed=speed, lang=lang)
        d = max(dur, round(LEAD + len(a) / sr + TAIL, 2))
        scenes.append((name, fn, d))
        seg = np.zeros(int(round(d * mod.FPS)) * sr // mod.FPS, dtype=np.float32)
        s = int(LEAD * sr); seg[s:s + len(a)] = a[: len(seg) - s]
        track.append(seg)
        print(name, dur, "->", d, flush=True)
    sf.write(f"{outdir}/voice.wav", np.concatenate(track), sr)
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor() as ex: list(ex.map(mod.render, *zip(*scenes)))
    with open(f"{outdir}/list.txt", "w") as f:
        for n, _, _ in scenes: f.write(f"file '{n}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{outdir}/list.txt",
                    "-c", "copy", f"{outdir}/silent.mp4"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{outdir}/silent.mp4", "-i", f"{outdir}/voice.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", f"{outdir}/{final}"], check=True)

if __name__ == "__main__":
    # New episodes: python3 narrate.py ep7  /  python3 narrate.py short7
    # The module must define SCENES, render(), FPS and NARRATION (scene name -> text), plus optional OUTPUT (file name).
    # Optional VOICE, SPEED, LANG (set them from the style: VOICE, SPEED, LANG = S.VOICE, S.SPEED, S.LANG).
    import importlib
    name = sys.argv[1]
    mod = importlib.import_module("render" if name == "ep1" and not os.path.exists("ep1.py") else name)
    if hasattr(mod, "NARRATION"):
        final = getattr(mod, "OUTPUT", f"{name}_narrated.mp4")
        build(mod, mod.NARRATION, name, final, 1.08 if name.startswith("short") else 1.0)
        print("OUTPUT", os.path.join(name, final))
        sys.exit(0)
    if sys.argv[1] == "ep1":
        import render; build(render, EP1, "out", "how_a_computer_boots_ep1_narrated.mp4", 1.0)
    elif sys.argv[1] == "ep2":
        import ep2; build(ep2, EP2, "ep2", "how_a_microcontroller_runs_code_ep2_narrated.mp4", 1.0)
    elif sys.argv[1] == "short2":
        import short2; build(short2, SHORT2, "short2", "ep2_short_one_address_narrated.mp4", 1.08)
    elif sys.argv[1] == "ep3":
        import ep3; build(ep3, EP3, "ep3", "what_happens_when_you_press_a_key_ep3_narrated.mp4", 1.0)
    elif sys.argv[1] == "short3":
        import short3; build(short3, SHORT3, "short3", "ep3_short_keyboard_never_sends_A_narrated.mp4", 1.08)
    elif sys.argv[1] == "ep4":
        import ep4; build(ep4, EP4, "ep4", "how_usb_knows_what_you_plugged_in_ep4_narrated.mp4", 1.0)
    elif sys.argv[1] == "short4":
        import short4; build(short4, SHORT4, "short4", "ep4_short_usb_who_are_you_narrated.mp4", 1.08)
    elif sys.argv[1] == "ep5":
        import ep5; build(ep5, EP5, "ep5", "i2c_vs_spi_vs_uart_ep5_narrated.mp4", 1.0)
    elif sys.argv[1] == "short5":
        import short5; build(short5, SHORT5, "short5", "ep5_short_3_languages_narrated.mp4", 1.08)
    elif sys.argv[1] == "ep6":
        import ep6; build(ep6, EP6, "ep6", "how_pwm_dims_an_led_ep6_narrated.mp4", 1.0)
    elif sys.argv[1] == "short6":
        import short6; build(short6, SHORT6, "short6", "ep6_short_pin_cant_do_half_narrated.mp4", 1.08)
    else:
        import short; build(short, SHORT, "short", "ep1_short_reset_vector_narrated.mp4", 1.08)

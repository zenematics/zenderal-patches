"""Voice the Rogue's three lines from the curator's recordings (Motion Array voice-over, 2026-11-19).

The Rogue (NPC 0x81F, voice type VT_Male_Bandit01 088CEB) speaks on the arena quest ZFW_Arena: five player topics
(Take me / What is it / Who are you / What walks in the fog / Anything to gain), the god-mode refusal on "Take me",
three random hellos and two goodbyes - 15 lines, LINES below (recording name -> INFO EditorID + response number;
--lines prints them with their texts). Each needs a .fuz (xWMA audio + FaceFX lip sync) at
    Sound\\Voice\\Zenderal - Fog Wood.esp\\VT_Male_Bandit01\\<quest[:10]>_<topic[:25 - len(quest[:10])]>_<00 + local ID>_<n>.fuz
The engine builds that name from the quest EditorID cut to 10 characters, the topic EditorID cut so both make 25, and
the response's FormID with the plugin index as 00 (measured on 219 of Enderal's own files in L - Voices.bsa: quest
BanditDialogue -> banditdial_ + 15 topic characters, FS_NQ01 -> 18, MQ05 -> 21). Without the file a line's subtitle
flashes by in a moment (the list has no Fuz Ro D'oh); with it he speaks and his mouth moves.

Pipeline, all from the Creation Kit install (tools.json papyrusCompiler's Root/Tools): the recording to 44.1 kHz
16-bit mono PCM (numpy), LipGenerator.exe (FaceFX, FonixData.cdf) with the record's own text -> .lip, xwmaencode.exe
-> .xwm, LIPFuzer.exe -> .fuz, copied into the voice folder of Zenderal - Patch Collection (not committed).

Usage:
    python src/FogWood/tools/03-install-rogue-voice.py --lines              # print the lines to record
    python src/FogWood/tools/03-install-rogue-voice.py --src <folder>       # <name>.wav or <name>.mp3 per line
        [--silent]        a line with no recording gets a silent .fuz of its reading time (subtitle stays up)
        [--target <MO2 mod folder>]   default <modlistRoot>/mods/Zenderal - Patch Collection
WAV (PCM 8/16/24/32-bit, any rate, mono or stereo) is read directly; MP3/M4A/OGG/FLAC through imageio-ffmpeg's
bundled ffmpeg (installed here; Motion Array exports MP3).
"""
import argparse
import glob
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
ESP_DIR = os.path.join(ROOT, 'src', 'FogWood', 'FogWoodESP')
TOOLS = json.load(open(os.path.join(ROOT, '.claude', 'config', 'tools.json'), encoding='utf-8-sig'))
CK_TOOLS = os.path.join(os.path.dirname(os.path.dirname(TOOLS['papyrusCompiler'])), 'Tools')
LIPGEN = os.path.join(CK_TOOLS, 'LipGen', 'LipGenerator', 'LipGenerator.exe')
LIPFUZER = os.path.join(CK_TOOLS, 'LipGen', 'LipFuzer', 'LIPFuzer.exe')
XWMAENCODE = os.path.join(CK_TOOLS, 'Audio', 'xwmaencode.exe')
PLUGIN = 'Zenderal - Fog Wood.esp'
VOICE_TYPE = 'VT_Male_Bandit01'
LINES = {                                   # recording name -> (INFO EditorID, response number)
    'take_1': ('ZFW_RogueTakeInfo', 1),       # Take me to the Fog Wood.
    'tgm_1': ('ZFW_RogueTakeRefuseInfo', 1),  #   ... with god mode on
    'what_1': ('ZFW_RogueWhatInfo', 1),       # What is the Fog Wood?
    'what_2': ('ZFW_RogueWhatInfo', 2),
    'who_1': ('ZFW_RogueWhoInfo', 1),         # Who are you?
    'who_2': ('ZFW_RogueWhoInfo', 2),
    'walks_1': ('ZFW_RogueWalksInfo', 1),     # What walks in the fog?
    'walks_2': ('ZFW_RogueWalksInfo', 2),
    'gain_1': ('ZFW_RogueGainInfo', 1),       # Is there anything to gain in there?
    'gain_2': ('ZFW_RogueGainInfo', 2),
    'hello_1': ('ZFW_RogueHelloInfo1', 1),    # greetings (random)
    'hello_2': ('ZFW_RogueHelloInfo2', 1),
    'hello_3': ('ZFW_RogueHelloInfo3', 1),
    'bye_1': ('ZFW_RogueByeInfo1', 1),        # goodbyes (random)
    'bye_2': ('ZFW_RogueByeInfo2', 1),
}
SOURCE_EXTS = ('.wav', '.mp3', '.m4a', '.ogg', '.flac')   # anything but WAV goes through imageio-ffmpeg's ffmpeg
RATE = 44100


def read_yaml_scalar(text, key):
    m = re.search(r'^%s: (.*)$' % re.escape(key), text, re.M)
    return m.group(1).strip() if m else None


def load_lines():
    """From the Spriggit YAML: quest EditorID, and per recording name the topic EditorID, response FormID and text."""
    quests = {}
    for f in glob.glob(os.path.join(ESP_DIR, 'Quests', '*.yaml')):
        t = open(f, encoding='utf-8').read()
        quests[read_yaml_scalar(t, 'FormKey')] = read_yaml_scalar(t, 'EditorID')
    infos = {}
    for d in glob.glob(os.path.join(ESP_DIR, 'DialogTopics', '*')):
        t = open(os.path.join(d, 'RecordData.yaml'), encoding='utf-8').read()
        topic, quest = read_yaml_scalar(t, 'EditorID'), quests[read_yaml_scalar(t, 'Quest')]
        for r in glob.glob(os.path.join(d, 'Responses', '*.yaml')):
            rt = open(r, encoding='utf-8').read()
            local = int(read_yaml_scalar(rt, 'FormKey').split(':')[0], 16)
            texts = {int(n): value.replace("''", "'")
                     for n, value in re.findall(r"ResponseNumber: (\d+)\n(?:.*\n)*?\s+Value: '((?:[^']|'')*)'", rt)}
            infos[read_yaml_scalar(rt, 'EditorID')] = (quest, topic, local, texts)
    out = {}
    for name, (info, n) in LINES.items():
        quest, topic, local, texts = infos[info]
        out[name] = (quest, topic, local, n, texts[n])
    return out


def decode_to_wav(src, dst):
    """MP3 (or anything ffmpeg reads) -> 44.1 kHz 16-bit mono WAV through imageio-ffmpeg's bundled ffmpeg."""
    try:
        import imageio_ffmpeg
    except ImportError:
        raise SystemExit('%s is not a WAV and imageio-ffmpeg is not installed to decode it (pip install imageio-ffmpeg)' % src)
    run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
         '-ac', '1', '-ar', str(RATE), '-sample_fmt', 's16', dst], cwd=os.path.dirname(dst))
    return dst


def voice_name(quest, topic, local, n):
    q = quest[:10]
    return ('%s_%s_%08X_%d' % (q, topic[:25 - len(q)], local, n)).lower()


def load_wav_mono_44k(path):
    """Any PCM WAV -> float32 mono at RATE."""
    with wave.open(path, 'rb') as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif width == 2:
        data = np.frombuffer(raw, dtype='<i2').astype(np.float32) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        data = ((b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)) ^ 0x800000) - 0x800000
        data = data.astype(np.float32) / 8388608.0
    elif width == 4:
        data = np.frombuffer(raw, dtype='<i4').astype(np.float32) / 2147483648.0
    else:
        raise SystemExit('%s: %d-byte samples are not PCM I can read; export 16-bit WAV' % (path, width))
    data = data.reshape(-1, ch).mean(axis=1)
    if rate != RATE:
        src_t = np.arange(len(data)) / float(rate)
        dst_t = np.arange(int(round(len(data) * RATE / float(rate)))) / float(RATE)
        data = np.interp(dst_t, src_t, data).astype(np.float32)
    peak = float(np.abs(data).max()) if len(data) else 0.0
    if peak > 0.99:
        data = data * (0.99 / peak)
    return data, (ch, width, rate)


def write_wav_16(path, data):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(data, -1.0, 1.0) * 32767.0).astype('<i2').tobytes())


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write((p.stdout + p.stderr).decode('cp1252', 'replace'))
        raise SystemExit('failed: %s' % ' '.join(cmd))
    return (p.stdout + p.stderr).decode('cp1252', 'replace')


def build_fuz(work, name, data, text):
    """wav -> lip + xwm -> fuz in `work`/<name>; returns the fuz path."""
    work = os.path.join(work, name)                 # one folder per line: LIPFuzer's -i filter matches nothing here
    os.makedirs(work, exist_ok=True)
    wav = os.path.join(work, name + '.wav')
    write_wav_16(wav, data)
    run([LIPGEN, wav, text], cwd=work)              # writes <name>.lip beside the wav (+ tmp16khz.wav in cwd)
    lip = os.path.join(work, name + '.lip')
    assert os.path.isfile(lip) and os.path.getsize(lip) > 0, 'LipGenerator wrote no .lip for ' + name
    run([XWMAENCODE, wav, os.path.join(work, name + '.xwm')], cwd=work)
    run([LIPFUZER, '-s', work, '-d', work, '--norec'], cwd=work)
    fuz = os.path.join(work, name + '.fuz')
    assert os.path.isfile(fuz) and os.path.getsize(fuz) > 0, 'LIPFuzer wrote no .fuz for ' + name
    return fuz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lines', action='store_true', help='print the lines to record and the file names they become')
    ap.add_argument('--src', help='folder with take_1.wav, what_1.wav, what_2.wav')
    ap.add_argument('--silent', action='store_true', help='a line without a recording gets a silent .fuz of its reading time')
    ap.add_argument('--target', default=os.path.join(TOOLS['modlistRoot'], 'mods', 'Zenderal - Patch Collection'))
    args = ap.parse_args()
    lines = load_lines()
    if args.lines or not args.src:
        print('The Rogue (VT_Male_Bandit01). Record each as <name>.wav or <name>.mp3:\n')
        for name, (quest, topic, local, n, text) in lines.items():
            print('%-7s  %s\n         -> Sound\\Voice\\%s\\%s\\%s.fuz\n' % (name, text, PLUGIN, VOICE_TYPE, voice_name(quest, topic, local, n)))
        if not args.src:
            return
    for exe in (LIPGEN, LIPFUZER, XWMAENCODE):
        assert os.path.isfile(exe), 'missing ' + exe
    assert os.path.isdir(args.target), args.target
    out_dir = os.path.join(args.target, 'Sound', 'Voice', PLUGIN, VOICE_TYPE)
    os.makedirs(out_dir, exist_ok=True)
    work = tempfile.mkdtemp(prefix='rogue_voice_')
    done = 0
    for name, (quest, topic, local, n, text) in lines.items():
        src = next((p for p in (os.path.join(args.src, name + ext) for ext in SOURCE_EXTS) if os.path.isfile(p)), None)
        if src:
            wav = src if src.lower().endswith('.wav') else decode_to_wav(src, os.path.join(work, name + '_src.wav'))
            data, fmt = load_wav_mono_44k(wav)
            how = '%s (%d ch, %d-bit, %d Hz, %.1f s)' % (os.path.basename(src), fmt[0], fmt[1] * 8, fmt[2], len(data) / float(RATE))
        elif args.silent:
            seconds = 0.6 + 0.07 * len(text)          # the subtitle's reading time
            data = np.zeros(int(seconds * RATE), dtype=np.float32)
            how = 'SILENT %.1f s' % seconds
        else:
            print('%-7s  no %s, skipped (use --silent for a silent placeholder)' % (name, os.path.basename(src)))
            continue
        fuz = build_fuz(work, name, data, text)
        dst = os.path.join(out_dir, voice_name(quest, topic, local, n) + '.fuz')
        shutil.copyfile(fuz, dst)
        print('%-7s  %s\n         -> %s (%d bytes)' % (name, how, dst, os.path.getsize(dst)))
        done += 1
    shutil.rmtree(work, ignore_errors=True)
    print('\n%d of %d lines voiced into %s' % (done, len(lines), out_dir))


if __name__ == '__main__':
    main()

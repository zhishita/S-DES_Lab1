"""将一次实际穷举的进度采样制作成慢速回放；画面时间来自原始计时。"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent


def main():
    record = json.loads((ROOT/'results/bruteforce_timeline.json').read_text(encoding='utf-8'))
    font_path = Path('C:/Windows/Fonts/consola.ttf')
    if not font_path.exists():
        font_path = Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')
    font = ImageFont.truetype(str(font_path),22) if font_path.exists() else ImageFont.load_default(size=22)
    small = ImageFont.truetype(str(font_path),16) if font_path.exists() else ImageFont.load_default(size=16)
    frames = []
    timeline = [{'checked':0,'elapsed_ms':0,'candidates':[]}] + record['timeline']
    for event in timeline:
        image = Image.new('RGB',(960,520),'#f4f7f3')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0,0,960,78),fill='#143d33')
        draw.text((30,25),'S-DES | exhaustive key search',font=font,fill='#eef3db')
        draw.text((30,103),'P = 10010111    C = 00111000    keyspace = 1024',font=font,fill='#143d33')
        draw.text((30,150),f"Checked: {event['checked']:4} / 1024",font=font,fill='#143d33')
        draw.text((30,187),f"Measured elapsed: {event['elapsed_ms']:.4f} ms",font=font,fill='#176955')
        draw.rectangle((30,231,930,251),fill='#dbe5d4')
        if event['checked']:
            draw.rectangle((30,231,30+int(900*event['checked']/1024),251),fill='#176955')
        draw.text((30,275),'Candidates: '+(', '.join(event['candidates']) or '(none yet)'),font=small,fill='#143d33')
        draw.text((30,322),'Started UTC:  '+record['started_utc'],font=small,fill='#536d63')
        draw.text((30,354),'Finished UTC: '+(record['finished_utc'] if event['checked']==1024 else '(running)'),font=small,fill='#536d63')
        draw.text((30,404),f"Actual full run: {record['elapsed_ms']:.4f} ms; all 1024 keys checked.",font=small,fill='#143d33')
        draw.text((30,446),'SLOW REPLAY of measured samples; animation duration is NOT runtime.',font=small,fill='#8d4b32')
        frames.append(image)
    frames[0].save(ROOT/'results/bruteforce.gif',save_all=True,append_images=frames[1:],
                   duration=[300]*(len(frames)-1)+[2200],loop=0,optimize=False)
    print('Generated results/bruteforce.gif from the real timestamp log')


if __name__ == '__main__':
    main()

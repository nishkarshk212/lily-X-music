# Copyright (c) 2025 ShreyamousX1025
# Licensed under the MIT License.
# This file is part of ShreyaMusic


import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from lily import config, logger
from lily.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        self.font1 = ImageFont.truetype("lily/helpers/Raleway-Bold.ttf", 30)
        self.font2 = ImageFont.truetype("lily/helpers/Inter-Light.ttf", 30)
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False)
        )
    async def close(self) -> None:
        await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f: f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            # 1. Create blurred background
            thumb = Image.open(temp).convert("RGBA")
            bg_thumb = thumb.resize(size, Image.Resampling.LANCZOS)
            blur = bg_thumb.filter(ImageFilter.GaussianBlur(25))
            image = ImageEnhance.Brightness(blur).enhance(.40)
            draw = ImageDraw.Draw(image)

            # 2. Create circular thumbnail with border
            # Crop to square first
            side = 400
            square_thumb = ImageOps.fit(thumb, (side, side), method=Image.LANCZOS)
            
            # Create circular mask
            mask = Image.new("L", (side, side), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, side, side), fill=255)
            
            # Apply mask to square thumb
            circular_thumb = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            circular_thumb.paste(square_thumb, (0, 0), mask=mask)
            
            # Paste circular thumb onto background
            pos_x, pos_y = 100, 160
            image.paste(circular_thumb, (pos_x, pos_y), circular_thumb)
            
            # Draw circular border (purple)
            border_width = 15
            draw.ellipse(
                (pos_x - border_width//2, pos_y - border_width//2, 
                 pos_x + side + border_width//2, pos_y + side + border_width//2),
                outline=(111, 23, 194), width=border_width
            )

            # 3. Draw Text
            # Title
            title_font = ImageFont.truetype("lily/helpers/Raleway-Bold.ttf", 45)
            # Wrap title if too long
            title_text = song.title[:45]
            if len(song.title) > 45:
                title_text += "..."
            
            draw.text((550, 200), title_text, font=title_font, fill=self.fill)
            
            # Channel and Views
            info_font = ImageFont.truetype("lily/helpers/Inter-Light.ttf", 30)
            info_text = f"{song.channel_name}  |  {song.view_count} views"
            draw.text((550, 310), info_text, font=info_font, fill=self.fill)

            # 4. Progress Bar
            bar_x1, bar_y = 550, 380
            bar_x2 = 1180
            bar_width = 8
            # Draw base line
            draw.line([(bar_x1, bar_y), (bar_x2, bar_y)], fill=(255, 255, 255, 100), width=bar_width)
            
            # Draw progress line (pink/purple)
            progress_x = bar_x1 + (bar_x2 - bar_x1) * 0.4 # Static 40% for visual
            draw.line([(bar_x1, bar_y), (progress_x, bar_y)], fill=(211, 84, 255), width=bar_width)
            
            # Draw progress knob
            knob_radius = 10
            draw.ellipse((progress_x - knob_radius, bar_y - knob_radius, 
                          progress_x + knob_radius, bar_y + knob_radius), fill=(211, 84, 255))

            # 5. Time indicators
            time_font = ImageFont.truetype("lily/helpers/Inter-Light.ttf", 25)
            draw.text((550, 410), "00:00", font=time_font, fill=self.fill)
            draw.text((bar_x2 - 50, 410), song.duration, font=time_font, fill=self.fill)

            # 6. Draw Playback Icons (simplified geometric shapes)
            icon_y = 480
            icon_color = (255, 255, 255)
            
            # Shuffle (two lines)
            draw.line([(550, icon_y + 10), (590, icon_y + 30)], fill=icon_color, width=3)
            draw.line([(550, icon_y + 30), (590, icon_y + 10)], fill=icon_color, width=3)
            
            # Back (Triangle + Line)
            draw.polygon([(680, icon_y + 20), (710, icon_y + 5), (710, icon_y + 35)], fill=icon_color)
            draw.line([(675, icon_y + 5), (675, icon_y + 35)], fill=icon_color, width=4)
            
            # Play (Triangle in circle)
            circle_center = (800, icon_y + 20)
            r = 30
            draw.ellipse((circle_center[0]-r, circle_center[1]-r, 
                          circle_center[0]+r, circle_center[1]+r), outline=icon_color, width=4)
            draw.polygon([(circle_center[0]-10, circle_center[1]-15), 
                          (circle_center[0]-10, circle_center[1]+15), 
                          (circle_center[0]+15, circle_center[1])], fill=icon_color)
            
            # Next (Triangle + Line)
            draw.polygon([(890, icon_y + 5), (890, icon_y + 35), (920, icon_y + 20)], fill=icon_color)
            draw.line([(925, icon_y + 5), (925, icon_y + 35)], fill=icon_color, width=4)
            
            # Loop (Circle with arrow - simplified to circle)
            draw.ellipse((1010, icon_y + 5, 1050, icon_y + 35), outline=icon_color, width=3)

            image.save(output)
            try: os.remove(temp)
            except Exception: pass
            return output
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB

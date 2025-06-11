import os
from PIL import Image, ImageDraw, ImageFont
from database import Database
from player import Player

class RankingSystem:
    def __init__(self):
        self.db = Database()

    def get_ranking(self, page=1, page_size=10):
        """获取排行榜数据"""
        offset = (page - 1) * page_size
        players_data = self.db.fetch_all(
            "SELECT qq_id, qq_nickname FROM players ORDER BY realm DESC, stage DESC, cultivation DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )
        ranking = []
        for data in players_data:
            if isinstance(data, tuple) and len(data) > 0:
                try:
                    qq_id, qq_nickname = data
                    player = Player(qq_id, qq_nickname)
                    ranking.append({
                        'name': player.name,
                        'faction': player.faction,
                        'power': player.calculate_power() if hasattr(player, 'calculate_power') else 0
                    })
                    player.close()
                except Exception as e:
                    print(f"处理玩家数据时出错，QQ ID: {qq_id if 'qq_id' in locals() else '未知'}, 错误信息: {e}")
            else:
                print(f"数据格式错误，跳过该数据: {data}")
        return ranking

    def generate_ranking_image(self, ranking, page):
        """生成排行榜图片"""
        image = Image.new('RGB', (300, len(ranking) * 30 + 50), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        # 指定支持中文的字体文件，这里假设系统中有 simhei.ttf 字体，你可以根据实际情况修改
        font_path = 'simhei.ttf'
        if not os.path.exists(font_path):
            print(f"字体文件 {font_path} 不存在，请检查。")
            return None
        font = ImageFont.truetype(font_path, 18)

        draw.text((10, 10), f"天骄榜 第 {page} 页", fill=(0, 0, 0), font=font)
        y = 40
        for i, player in enumerate(ranking, start=(page - 1) * 10 + 1):
            text = f"{i}. {player['name']} ({player['faction']}阵营)"
            draw.text((10, y), text, fill=(0, 0, 0), font=font)
            y += 30

        # 使用绝对路径保存图片
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, f"ranking_page_{page}.png")
        image.save(image_path)
        return image_path
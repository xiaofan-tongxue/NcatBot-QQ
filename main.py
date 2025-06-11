from ncatbot.core import BotClient, GroupMessage, MessageChain, Image
from ncatbot.utils import get_log
from combat import CombatSystem
from player import Player
from cultivation import CultivationSystem
from battle import BattleSystem
from alchemy import AlchemySystem
from forging import ForgingSystem
from ranking import RankingSystem
from talisman import TalismanSystem
from farming import FarmingSystem
from quest import QuestSystem
from database import Database
import re
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
import textwrap

# 初始化数据库
db = Database()
db.close()

# 创建机器人
bot = BotClient()
_log = get_log()

# 初始化系统
cultivation_system = CultivationSystem()
battle_system = BattleSystem()
alchemy_system = AlchemySystem()
forging_system = ForgingSystem()
talisman_system = TalismanSystem()
farming_system = FarmingSystem()
quest_system = QuestSystem()
combat_system = CombatSystem()

# 帮助信息
ZHILIG = """1. 修炼系统指令

1.1 修炼指令

指令格式：修炼 [小时数]

参数说明：小时数为可选，默认为1小时，范围1-24小时

功能说明：进行修炼获取修为值，修炼效率受灵根影响

示例：

修炼 - 修炼1小时

修炼 5 - 修炼5小时

1.2 突破指令

指令格式：突破

功能说明：尝试突破当前境界到下一境界，需要达到大圆满且有突破丹药

注意事项：突破有失败风险，失败可能导致修为倒退或受伤

示例：

突破 - 尝试突破当前境界

1.3 状态指令

指令格式：状态

功能说明：查看玩家当前状态信息，包括境界、修为、属性、灵根等

示例：

状态 - 显示玩家当前状态

2. 战斗系统指令

2.1 战斗指令

指令格式：战斗 @对手QQ

参数说明：必须@一个有效的QQ号

功能说明：与指定玩家进行战斗，胜负由属性、装备和五行相克决定

注意事项：每30分钟只能进行一次战斗

示例：

战斗 @123456 - 与QQ123456的玩家战斗

2.2 战斗记录指令

指令格式：战斗记录

功能说明：查看最近5场战斗记录

示例：

战斗记录 - 显示最近5场战斗结果

3. 生产系统指令

3.1 炼丹相关指令

3.1.1 丹方指令

指令格式：丹方

功能说明：查看当前可炼制的丹药配方

示例：

丹方 - 显示可炼制的丹药列表

3.1.2 炼丹指令

指令格式：炼丹 [丹药名]

参数说明：丹药名必须为丹方列表中存在的名称

功能说明：炼制指定丹药，需要消耗相应材料

注意事项：炼丹可能失败甚至炸炉

示例：

炼丹 筑基丹 - 炼制筑基丹

3.2 炼器相关指令

3.2.1 器方指令

指令格式：器方

功能说明：查看当前可炼制的装备配方

示例：

器方 - 显示可炼制的装备列表

3.2.2 炼器指令

指令格式：炼器 [装备名]

参数说明：装备名必须为器方列表中存在的名称

功能说明：炼制指定装备，需要消耗相应材料

注意事项：炼器可能失败甚至造成伤害

示例：

炼器 青钢剑 - 炼制青钢剑

3.3 符箓相关指令

3.3.1 符方指令

指令格式：符方

功能说明：查看当前可制作的符箓配方

示例：

符方 - 显示可制作的符箓列表

3.3.2 制符指令

指令格式：制符 [符箓名]

参数说明：符箓名必须为符方列表中存在的名称

功能说明：制作指定符箓，需要消耗相应材料

注意事项：制符可能失败甚至灵力反噬

示例：

制符 火球符 - 制作火球符

3.4 灵植相关指令

3.4.1 灵植指令

指令格式：灵植

功能说明：查看可种植的灵植列表

示例：

灵植 - 显示可种植的灵植信息

3.4.2 种植指令

指令格式：种植 [灵植名] [地块号]

参数说明：

灵植名：必须为灵植列表中存在的名称

地块号：1-5之间的数字

功能说明：在指定地块种植灵植，需要相应种子

示例：

种植 灵草 1 - 在1号地块种植灵草

3.4.3 查看灵植指令

指令格式：查看灵植

功能说明：查看当前种植的灵植生长状态

示例：

查看灵植 - 显示所有地块的灵植状态

3.4.4 收获指令

指令格式：收获 [地块号]

参数说明：地块号为1-5之间的数字

功能说明：收获指定地块已成熟的灵植

示例：

收获 1 - 收获1号地块的灵植

3.4.5 加速指令

指令格式：加速 [地块号] [灵水/生长符]

参数说明：

地块号：1-5之间的数字

加速物品：灵水或生长符

功能说明：使用物品加速灵植生长

示例：

加速 1 灵水 - 使用灵水加速1号地块灵植生长

4. 任务系统指令

4.1 可接任务指令

指令格式：可接任务

功能说明：查看当前可接受的任务列表

示例：

可接任务 - 显示可接任务

4.2 接受任务指令

指令格式：接受任务 [任务名]

参数说明：任务名必须为可接任务列表中存在的名称

功能说明：接受指定任务

示例：

接受任务 初入仙途 - 接受"初入仙途"任务

4.3 任务进度指令

指令格式：任务进度

功能说明：查看当前进行中的任务及其进度

示例：

任务进度 - 显示所有进行中任务

4.4 完成任务指令

指令格式：完成任务 [任务名]

参数说明：任务名必须为已完成的任务名称

功能说明：提交已完成的任务获取奖励

示例：

完成任务 初入仙途 - 完成"初入仙途"任务

5. 其他指令

5.1 帮助指令

指令格式：帮助

功能说明：显示完整的指令帮助信息

示例：

帮助 - 显示所有指令说明

指令使用注意事项

所有指令均需在QQ群中发送，@机器人+指令或直接发送指令

指令参数中的方括号[]表示可选参数，实际输入时不需输入方括号

部分指令有冷却时间限制，如战斗、修炼等

生产类指令需要先学习相应配方，并准备足够材料

任务系统会随着境界提升解锁更多内容

灵根属性会显著影响各系统的效果

指令快捷参考表

类别	指令	功能简述

修炼	修炼 [小时数]	进行修炼获取修为

修炼	突破	尝试突破当前境界

修炼	状态	查看玩家当前状态

战斗	战斗 @对手	与指定玩家战斗

战斗	战斗记录	查看战斗历史

炼丹	丹方	查看可炼制丹药

炼丹	炼丹 [丹药名]	炼制指定丹药

炼器	器方	查看可炼制装备

炼器	炼器 [装备名]	炼制指定装备

符箓	符方	查看可制作符箓

符箓	制符 [符箓名]	制作指定符箓

灵植	灵植	查看可种植灵植

灵植	种植 [灵植] [地块]	种植灵植

灵植	查看灵植	查看灵植状态

灵植	收获 [地块]	收获灵植

灵植	加速 [地块] [物品]	加速灵植生长

任务	可接任务	查看可接任务

任务	接受任务 [任务名]	接受指定任务

任务	任务进度	查看任务进度

任务	完成任务 [任务名]	提交完成任务

其他	帮助	显示帮助信息"""

HELP_MSG = """《仙魔道》修仙指南：

【修炼系统】

1. 修炼 - 进行修炼10分钟 修炼出关 - 修炼完成并出关

2. 突破 - 尝试突破当前境界

3. 状态 - 查看自身状态

【战斗系统】

4. 战斗 @对手 - 与其他修士切磋

5. 战斗记录 - 查看最近的战斗记录


【生产系统】

6. 丹方 - 查看可炼制丹药

7. 炼丹 [丹药名] - 炼制指定丹药

8. 器方 - 查看可炼制装备

9. 炼器 [装备名] - 炼制指定装备

10. 符方 - 查看可制作符箓

11. 制符 [符箓名] - 制作指定符箓

12. 灵植 - 查看可种植灵植

13. 种植 [灵植名] [地块号] - 在指定地块种植灵植

14. 查看灵植 - 查看灵植生长状态

15. 收获 [地块号] - 收获指定地块的灵植

16. 加速 [地块号] [灵水/生长符] - 加速灵植生长


【任务系统】


17. 可接任务 - 查看可接的任务

18. 接受任务 [任务名] - 接受指定任务

19. 任务进度 - 查看当前任务进度

20. 完成任务 [任务名] - 完成指定任务


【妖兽系统】

21.妖兽列表 -查看妖兽信息

22.挑战妖兽 - 挑战妖兽可获得兽核


【其他】

23. 修仙指南 - 显示此修仙文档

24. 修仙指令 - 显示所有指令大全"""


def generate_help_image(wenben):
    # 图片宽度
    image_width = 800
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)
    font_size = 20  # 字体大小
    line_spacing = 25
    paragraph_spacing = 30  # 段落间距

    # 指定支持中文的字体文件，这里假设系统中有 simhei.ttf 字体，你可以根据实际情况修改
    font = ImageFont.truetype('simhei.ttf', font_size)

    # 自动换行处理文本，同时按段落分割
    paragraphs = wenben.split('\n\n')
    lines = []
    for paragraph in paragraphs:
        para_lines = textwrap.wrap(paragraph, width=image_width // (font_size // 2))
        lines.extend(para_lines)
        lines.append('')  # 为每个段落添加一个空行作为间隔

    # 计算所需的图片高度
    image_height = 20 + (len(lines) - 1) * line_spacing + (paragraphs.count('\n\n')) * paragraph_spacing

    # 创建一个新的空白图片
    img = PILImage.new('RGB', (image_width, image_height), background_color)
    draw = ImageDraw.Draw(img)

    y_text = 20
    for line in lines:
        if line:
            draw.text((20, y_text), line, fill=text_color, font=font)
            y_text += line_spacing
        else:
            y_text += paragraph_spacing  # 遇到空行，增加段落间距

    # 保存图片
    image_path = "help_message.png"
    img.save(image_path)
    return image_path


# 注册群消息事件
@bot.group_event()
async def on_group_message(msg: GroupMessage):
    _log.info(f"收到群消息: {msg.raw_message}")

    try:
        if hasattr(msg.sender, 'user_id'):
            user_qq = str(msg.sender.user_id)
            qq_nickname = getattr(msg.sender, 'nickname', f"无名修士{user_qq[-4:]}")
            
            # 清理昵称中的非法字符
            qq_nickname = "".join(c for c in qq_nickname if c.isprintable() and not c.isspace())
            qq_nickname = qq_nickname[:20]  # 限制最大长度
            
            # 创建玩家实例，强制使用QQ昵称
            player = Player(user_qq, qq_nickname)
        else:
            _log.error(f"消息发送者对象缺少 user_id 属性: {msg.sender}")
            await bot.api.post_group_msg(msg.group_id, text="系统错误，请稍后再试")
            return

    except Exception as e:
        _log.error(f"处理消息时出错: {e}")
        await bot.api.post_group_msg(msg.group_id, text="系统错误，请稍后再试")
        return

    # 指令解析
    text = msg.raw_message.strip()
    group_id = msg.group_id
    result = None

    try:
        if text.startswith(("修炼", "突破", "状态", "战斗", "丹方", "炼丹",
                          "器方", "炼器", "符方", "制符", "灵植", "种植",
                          "查看灵植", "收获", "加速", "可接任务", "接受任务",
                          "任务进度", "完成任务", "修仙指南", "修仙指令",
                          "妖兽", "查看储物袋", "查看状态","赠送道具", "天骄榜")):

            # 修改此处，传入 qq_nickname 参数
            player = Player(user_qq, qq_nickname)
            if not player.name:  # 如果是新玩家
                player.initialize_new_player(qq_nickname)
                player.update()

            if text.startswith("修炼"):
                if "出关" in text:
                    # 修炼出关
                    result = cultivation_system.complete_cultivate(player)
                else:
                    # 开始修炼
                    match = re.match(r"修炼\s*(\d+)", text)
                    if match:
                        await bot.api.post_group_msg(group_id, text="现在修炼需要单独使用'修炼'指令开始，10分钟后使用'修炼出关'完成")
                    else:
                        result = cultivation_system.start_cultivate(player)

            elif text == "突破":
                result = cultivation_system.attempt_breakthrough(player)

            elif text == "状态":
                # 状态
                result = player.get_status()

            elif text.startswith("战斗"):
                # 战斗 @对手 或 战斗记录
                if "记录" in text:
                    # 查看战斗记录
                    try:
                        # 创建新的数据库连接
                        temp_db = Database()
                        logs = temp_db.fetch_all(
                            "SELECT opponent_id, result, battle_time FROM battle_logs WHERE qq_id = ? ORDER BY battle_time DESC LIMIT 5",
                            (user_qq,)
                        )
                        temp_db.close()  # 关闭临时数据库连接

                        if not logs:
                            result = "你还没有战斗记录"
                        else:
                            result = "最近5场战斗记录:\n"
                            for log in logs:
                                opponent = log[0]
                                result += f"对手: {opponent}, 结果: {log[1]}, 时间: {log[2]}\n"
                    except Exception as e:
                        result = f"查询战斗记录失败: {str(e)}"
                else:
                    # 解析对手QQ
                    match = re.search(r"\[CQ:at,qq=(\d+)\]", text)
                    if not match:
                        await bot.api.post_group_msg(group_id, text="请指定对手，格式: 战斗 @对手QQ")
                        return
                    defender_id = match.group(1)
                    result = battle_system.battle(player, defender_id)

            elif text == "丹方":
                # 查看丹方
                result = alchemy_system.list_recipes(player)

            elif text.startswith("炼丹"):
                # 炼丹 [丹药名]
                pill_name = text[2:].strip()
                if not pill_name:
                    await bot.api.post_group_msg(group_id, text="请指定要炼制的丹药名称")
                    return
                result = alchemy_system.refine_pill(player, pill_name)

            elif text == "器方":
                # 查看炼器配方
                result = forging_system.list_recipes(player)

            elif text.startswith("炼器"):
                # 炼器 [装备名]
                item_name = text[2:].strip()
                if not item_name:
                    await bot.api.post_group_msg(group_id, text="请指定要炼制的装备名称")
                    return
                result = forging_system.forge_item(player, item_name)

            elif text == "符方":
                # 查看符箓配方
                result = talisman_system.list_recipes(player)

            elif text.startswith("制符"):
                # 制符 [符箓名]
                talisman_name = text[2:].strip()
                if not talisman_name:
                    await bot.api.post_group_msg(group_id, text="请指定要制作的符箓名称")
                    return
                result = talisman_system.make_talisman(player, talisman_name)

            elif text == "灵植":
                # 查看可种植灵植
                result = farming_system.list_plants()

            elif text.startswith("种植"):
                # 种植 [灵植名] [地块号]
                match = re.match(r"种植\s+(\S+)\s+(\d+)", text)
                if not match:
                    await bot.api.post_group_msg(group_id, text="格式: 种植 [灵植名] [地块号(1-5)]")
                    return
                plant_name, plot_id = match.groups()
                plot_id = int(plot_id)
                if plot_id < 1 or plot_id > 5:
                    await bot.api.post_group_msg(group_id, text="地块号必须在1-5之间")
                    return
                result = farming_system.plant_seed(player, plant_name, plot_id)

            elif text == "查看灵植":
                # 查看灵植状态
                result = farming_system.check_plants(player)

            elif text.startswith("收获"):
                # 收获 [地块号]
                match = re.match(r"收获\s+(\d+)", text)
                if not match:
                    await bot.api.post_group_msg(group_id, text="格式: 收获 [地块号(1-5)]")
                    return
                plot_id = int(match.group(1))
                if plot_id < 1 or plot_id > 5:
                    await bot.api.post_group_msg(group_id, text="地块号必须在1-5之间")
                    return
                result = farming_system.harvest_plant(player, plot_id)

            elif text.startswith("加速"):
                # 加速 [地块号] [灵水/生长符]
                match = re.match(r"加速\s+(\d+)\s+(\S+)", text)
                if not match:
                    await bot.api.post_group_msg(group_id, text="格式: 加速 [地块号(1-5)] [灵水/生长符]")
                    return
                plot_id, item_id = match.groups()
                plot_id = int(plot_id)
                if plot_id < 1 or plot_id > 5:
                    await bot.api.post_group_msg(group_id, text="地块号必须在1-5之间")
                    return
                result = farming_system.accelerate_growth(player, plot_id, item_id)

            elif text == "可接任务":
                # 查看可接任务
                result = quest_system.get_available_quests(player)

            elif text.startswith("接受任务"):
                # 接受任务 [任务名]
                quest_name = text[4:].strip()
                if not quest_name:
                    await bot.api.post_group_msg(group_id, text="请指定要接受的任务名称")
                    return
                result = quest_system.accept_quest(player, quest_name)

            elif text == "任务进度":
                # 查看任务进度
                result = quest_system.check_quests(player)

            elif text.startswith("完成任务"):
                # 完成任务 [任务名]
                quest_name = text[4:].strip()
                if not quest_name:
                    await bot.api.post_group_msg(group_id, text="请指定要完成的任务名称")
                    return
                result = quest_system.complete_quest(player, quest_name)

            elif text.startswith("妖兽列表"):
                result = combat_system.list_monsters(player)
            elif text.startswith("妖兽挑战"):
                monster_name = text[4:].strip()
                if not monster_name:
                    await bot.api.post_group_msg(group_id, text="请指定要挑战的妖兽名称")
                    return
                    
                # 检查玩家气血
                if player.health <= 10:
                    await bot.api.post_group_msg(group_id, text="你的气血不足，无法挑战妖兽")
                    return
                    
                result = combat_system.battle_monster(player, monster_name)
                await bot.api.post_group_msg(group_id, at=user_qq, text=result)

            elif text == "查看储物袋":
                result = player.get_inventory()
            
            elif text.startswith("查看状态"):
                # 解析对手QQ
                match = re.search(r"\[CQ:at,qq=(\d+)\]", text)
                if not match:
                    await bot.api.post_group_msg(group_id, text="请指定要查看的玩家，格式: 查看状态 @玩家QQ")
                    return
                target_id = match.group(1)
                target_player = Player(target_id)
                if not target_player.name:
                    target_player.close()
                    result = "找不到该玩家"
                else:
                    result = target_player.get_status()
                    target_player.close()

            elif text == "修仙指南":
                # 修仙指南
                image_path = generate_help_image(HELP_MSG)
                message = MessageChain([
                    Image(image_path)
                ])
                await bot.api.post_group_msg(group_id, rtf=message)

            elif text == "修仙指令":
                # 修仙指令
                image_path = generate_help_image(ZHILIG)
                message = MessageChain([  # 修正此处的 MemoryError 为 MessageChain
                    Image(image_path)
                ])
                await bot.api.post_group_msg(group_id, rtf=message)
            
            elif text.startswith("赠送道具"):
                # 解析指令
                match = re.search(r"赠送道具\s+(\S+)\s*(\d*)\s*\[CQ:at,qq=(\d+)\]", text)
                if not match:
                    await bot.api.post_group_msg(group_id, text="请使用正确的格式: 赠送道具[道具名][数量（没有填写数量默认为1）][艾特人员的QQ]")
                    return
                item_name = match.group(1)
                count_str = match.group(2)
                target_qq = match.group(3)

                # 处理数量
                count = int(count_str) if count_str else 1

                # 创建目标玩家对象
                target_player = Player(target_qq)

                # 转移道具
                result = player.transfer_item(item_name, count, target_player)

                # 关闭目标玩家数据库连接
                target_player.close()

            elif text.startswith("使用"):
                item_name = text[2:].strip()
                if item_name.endswith("配方"):
                    # 检查是否是配方
                    recipe_data = player.db.fetch_one(
                        "SELECT is_recipe, recipe_type FROM items WHERE item_id = ? AND qq_id = ?",
                        (item_name, player.qq_id)
                    )
                    
                    if recipe_data and recipe_data[0]:
                        recipe_type = recipe_data[1]
                        # 移除配方物品
                        if player.remove_item(item_name, 1):
                            # 学习配方
                            recipe_name = item_name.replace("配方", "")
                            if recipe_type == "alchemy":
                                success = alchemy_system.learn_recipe(player, recipe_name)
                            elif recipe_type == "forging":
                                success = forging_system.learn_recipe(player, recipe_name)
                            elif recipe_type == "talisman":
                                success = talisman_system.learn_recipe(player, recipe_name)
                                
                            if success:
                                result = f"你学会了{recipe_name}的炼制方法！"
                            else:
                                result = "学习配方失败"
                        else:
                            result = "你没有这个配方"
                    else:
                        result = "这不是有效的配方"
                else:
                    result = "使用物品指令格式: 使用 [物品名]"
                    
                await bot.api.post_group_msg(group_id, at=user_qq, text=result)

            elif text == "天骄榜":
                ranking_system = RankingSystem()
                ranking = ranking_system.get_ranking()
                result = "天骄榜:\n\n"
                for i, player_info in enumerate(ranking, start=1):
                    result += f"{i}. {player_info['name']} ({player_info['faction']}阵营) 战力: {player_info['power']}\n\n"
                image_path = generate_help_image(result)
                message = MessageChain([  # 修正此处的 MemoryError 为 MessageChain
                    Image(image_path)
                ])
                await bot.api.post_group_msg(group_id, rtf=message)
                result = False

            
            # 仅当有结果时才回复
            if result:
                result += "\n"
                await bot.api.post_group_msg(group_id, at=user_qq, text= result)
            player.close()

        # 非指令消息不处理，不回复
        else:
            player.close()

    except Exception as e:
        _log.error(f"处理命令时出错: {e}")
        # 仅在处理指令时出错才回复错误信息
        if text.startswith(("修炼", "突破", "状态", "战斗", "丹方", "炼丹",
                            "器方", "炼器", "符方", "制符", "灵植", "种植",
                            "查看灵植", "收获", "加速", "可接任务", "接受任务",
                            "任务进度", "完成任务", "修仙指南", "修仙指令",
                            "妖兽", "查看储物袋", "查看状态","赠送道具", "天骄榜")):
            await bot.api.post_group_msg(group_id, text="处理命令时出错，请稍后再试")


# 启动机器人
if __name__ == "__main__":
    bot.run(bt_uin="3690856267", bt_pwd="FANYU30CURRY")
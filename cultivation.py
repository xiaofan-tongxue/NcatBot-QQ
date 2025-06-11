from datetime import datetime, timedelta
import random

from player import Player

class CultivationSystem:
    def __init__(self):
        self.daily_limit = 3  # 每日最多修炼3次
        self.cultivation_duration = timedelta(minutes=10)  # 每次修炼10分钟
        self.breakthrough_items = {
            '炼体境': '筑基丹',
            '蚀骨境': '聚煞丹',
            '练气境': '凝气丹',
            '聚煞境': '魔煞丹',
            '筑基境': '金丹',
            '铸魔台': '魔心丹',
            '金丹境': '元婴丹',
            '结魔丹': '化魔丹',
            '元婴境': '化神丹',
            '化魔胎': '炼狱丹',
            '化神境': '渡劫丹',
            '炼狱境': '逆天丹',
            '渡劫境': '大乘丹',
            '逆天境': '灭世丹'
        }
        
    def start_cultivate(self, player: Player) -> str:
        """开始修炼"""
        # 检查是否已在修炼中
        if player.is_cultivating:
            return "你已经在修炼中了"
            
        # 检查今日修炼次数
        today = datetime.now().strftime("%Y-%m-%d")
        if player.last_cultivate and player.last_cultivate.startswith(today):
            if player.daily_cultivate_count >= self.daily_limit:
                return f"今日已修炼{player.daily_cultivate_count}次，最多只能修炼{self.daily_limit}次"
        
        player.start_cultivation()
        return "你开始闭关修炼，10分钟后将出关获得修为"
        
    def complete_cultivate(self, player: Player) -> str:
        """完成修炼"""
        if not player.is_cultivating:
            return "你当前没有在修炼"
            
        # 检查修炼时间是否足够
        start_time = datetime.strptime(player.cultivate_start_time, "%Y-%m-%d %H:%M:%S")
        if datetime.now() < start_time + self.cultivation_duration:
            remaining = (start_time + self.cultivation_duration) - datetime.now()
            return f"修炼尚未完成，还需等待{remaining.seconds // 60}分{remaining.seconds % 60}秒"
        
        # 计算修炼收益
        cultivation_gain = self.calculate_cultivation_gain(player)
        player.cultivation += cultivation_gain
        player.complete_cultivation()
        
        # 随机事件
        event = self.random_cultivation_event(player)
        
        result = f"修炼完成！获得{cultivation_gain:.1f}点修为。\n"
        result += f"当前境界进度: {player.get_cultivation_progress():.1f}%\n"
        if event:
            result += f"\n修炼过程中: {event}"
            
        return result
        
    def calculate_cultivation_gain(self, player: Player) -> float:
        """计算修炼获得的修为"""
        realm_list = player.get_current_realm_list()
        realm_index = realm_list.index(player.realm)
        base_gain = 10 * (2 ** realm_index)
        
        # 灵根加成
        efficiency = self.calculate_efficiency(player)
        return base_gain * efficiency
        
    def calculate_efficiency(self, player: Player) -> float:
        """计算修炼效率"""
        if not player.roots:
            return 0.5  # 无灵根效率低下
            
        # 混沌灵根特殊处理
        if '混沌' in player.roots:
            return 1.0  # 混沌灵根全系亲和，效率最高
            
        # 单灵根最高效率
        if len(player.roots) == 1:
            return 0.8 + (list(player.roots.values())[0] / 500)  # 80%-100%
            
        # 多灵根效率降低
        avg_purity = sum(player.roots.values()) / len(player.roots)
        return 0.5 + (avg_purity / 500)  # 50%-70%
        
    def random_cultivation_event(self, player: Player) -> str:
        """随机修炼事件"""
        events = [
            (0.1, "心有所悟，修为小有精进", lambda p: setattr(p, 'cultivation', p.cultivation * 1.1)),
            (0.05, "灵气紊乱，修为略有倒退", lambda p: setattr(p, 'cultivation', max(0, p.cultivation * 0.9))),
            (0.01, "顿悟！修为大幅提升", lambda p: setattr(p, 'cultivation', p.cultivation * 1.5)),
            (0.01, "走火入魔，身受重伤", lambda p: setattr(p, 'health', max(1, p.health - 20))),
            (0.83, "无特别事件发生", lambda p: None)
        ]
        
        # 根据权重选择事件
        total = sum(w for w, _, _ in events)
        rand = random.uniform(0, total)
        upto = 0
        for w, desc, func in events:
            if upto + w >= rand:
                func(player)
                return desc if desc != "无特别事件发生" else ""
            upto += w
        return ""
        
    def attempt_breakthrough(self, player: Player) -> str:
        """尝试突破境界"""
        # 检查是否可以突破
        can_breakthrough, msg = player.can_breakthrough()
        if not can_breakthrough:
            return msg
            
        # 检查突破冷却
        if player.last_breakthrough_attempt:
            last_time = datetime.strptime(player.last_breakthrough_attempt, "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - last_time) < timedelta(hours=1):
                return "突破失败后需要等待1小时才能再次尝试"
        
        # 检查突破物品
        required_item = self.breakthrough_items.get(player.realm)
        if required_item and (required_item not in player.items or player.items[required_item]['count'] < 1):
            return f"突破需要{required_item}，你尚未拥有此物品"
            
        # 计算突破成功率
        success_rate = self.calculate_breakthrough_rate(player)
        success = random.random() < success_rate
        
        # 更新最后突破尝试时间
        player.last_breakthrough_attempt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if success:
            # 突破成功
            next_realm = player.get_next_realm()
            if not next_realm:
                return "已到达最高境界，无法继续突破"
                
            player.realm = next_realm
            player.stage = "初期"
            player.cultivation = 0
            player.max_health += 20
            player.health = player.max_health
            player.max_mana += 20
            player.mana = player.max_mana
            player.attack += 5
            player.defense += 3
            
            if required_item:
                player.remove_item(required_item, 1)
            
            player.update()
            return f"恭喜！你成功突破到{next_realm}初期！"
        else:
            # 突破失败
            penalties = [
                (0.5, "修为倒退", lambda p: setattr(p, 'cultivation', max(0, p.cultivation - 100))),
                (0.3, "心魔入侵，身受重伤", lambda p: setattr(p, 'health', max(1, p.health - 30))),
                (0.2, "无大碍", lambda p: None)
            ]
            
            # 根据权重选择惩罚
            total = sum(w for w, _, _ in penalties)
            rand = random.uniform(0, total)
            upto = 0
            for w, desc, func in penalties:
                if upto + w >= rand:
                    func(player)
                    player.update()
                    return f"突破失败！{desc}。请继续积累修为再试。"
                upto += w
            return "突破失败！请继续积累修为再试。"
            
    def calculate_breakthrough_rate(self, player: Player) -> float:
        """计算突破成功率"""
        base_rate = 0.5
        realm_list = player.get_current_realm_list()
        realm_index = realm_list.index(player.realm)
        
        # 境界越高成功率越低
        rate = base_rate * (0.9 ** realm_index)
        
        # 灵根纯度加成
        if player.roots:
            max_purity = max(player.roots.values())
            rate += max_purity / 500  # 最高加成20%
            
        # 仙魔阵营加成
        if player.faction == '仙域' and player.realm in player.REALMS['仙域']:
            rate += 0.1
        elif player.faction == '魔渊' and player.realm in player.REALMS['魔渊']:
            rate += 0.1
            
        return min(0.9, max(0.1, rate))  # 保持在10%-90%之间
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBOX直播源自动爬虫 - GitHub Actions版
自动从官方源爬取直播源，生成M3U/TXT/JSON
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path

class LiveSourceFetcher:
    """直播源获取器"""
    
    def __init__(self):
        self.m3u_content = "#EXTM3U\n"
        self.txt_content = ""
        self.json_data = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
    
    def add_channel(self, name, url):
        """添加频道"""
        self.m3u_content += f"#EXTINF:-1,{name}\n{url}\n"
        self.txt_content += f"{name},{url}\n"
        self.json_data.append({
            "name": name,
            "url": url,
            "timestamp": datetime.now().isoformat()
        })
        print(f"✓ 添加: {name}")
    
    def fetch_from_fanmingming(self):
        """从fanmingming源爬取直播源"""
        print("📺 正在从fanmingming爬取直播源...")
        
        try:
            # fanmingming的M3U源
            url = "https://raw.fastgit.org/fanmingming/live/main/tv/m3u/global.m3u"
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                current_name = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('#EXTINF'):
                        # 提取频道名
                        match = re.search(r',(.+)$', line)
                        if match:
                            current_name = match.group(1)
                    elif line and not line.startswith('#') and current_name:
                        # 这是URL行
                        self.add_channel(current_name, line)
                        current_name = ""
                
                print(f"✅ fanmingming源: 成功获取 {len(self.json_data)} 个频道")
                return True
        except Exception as e:
            print(f"❌ fanmingming源获取失败: {e}")
            return False
    
    def fetch_from_github_yousq(self):
        """从yousq的GitHub源爬取"""
        print("📺 正在从yousq源爬取直播源...")
        
        try:
            url = "https://raw.fastgit.org/yousq/iptv/main/iptv.m3u"
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                current_name = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('#EXTINF'):
                        match = re.search(r',(.+)$', line)
                        if match:
                            current_name = match.group(1)
                    elif line and not line.startswith('#') and current_name:
                        self.add_channel(current_name, line)
                        current_name = ""
                
                print(f"✅ yousq源: 成功获取 {len(self.json_data)} 个频道")
                return True
        except Exception as e:
            print(f"❌ yousq源获取失败: {e}")
            return False
    
    def fetch_domestic_ips(self):
        """添加国内运营商IP源"""
        print("📺 正在添加国内IP源...")
        
        domestic_sources = {
            "CCTV-1 综合": "http://39.135.55.105:6610/PLTV/88888910/224/3221225618/index.m3u8",
            "CCTV-2 财经": "http://39.135.55.105:6610/PLTV/88888910/224/3221225619/index.m3u8",
            "CCTV-3 综艺": "http://39.135.55.105:6610/PLTV/88888910/224/3221225620/index.m3u8",
            "CCTV-4 国际": "http://39.135.55.105:6610/PLTV/88888910/224/3221225621/index.m3u8",
            "CCTV-5 体育": "http://39.135.55.105:6610/PLTV/88888910/224/3221225622/index.m3u8",
            "浙江卫视": "http://39.135.55.105:6610/PLTV/88888910/224/3221225814/index.m3u8",
            "江苏卫视": "http://39.135.55.105:6610/PLTV/88888910/224/3221225815/index.m3u8",
            "湖南卫视": "http://39.135.55.105:6610/PLTV/88888910/224/3221225816/index.m3u8",
        }
        
        for name, url in domestic_sources.items():
            self.add_channel(name, url)
        
        print(f"✅ 国内IP源: 添加 {len(domestic_sources)} 个频道")
    
    def save_results(self):
        """保存结果"""
        print("💾 正在保存文件...")
        
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # 保存M3U
        m3u_file = data_dir / 'result.m3u'
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write(self.m3u_content)
        print(f"✓ M3U文件: {m3u_file}")
        
        # 保存TXT
        txt_file = data_dir / 'result.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(self.txt_content)
        print(f"✓ TXT文件: {txt_file}")
        
        # 保存JSON
        json_file = data_dir / 'sources.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': len(self.json_data),
                'channels': self.json_data
            }, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON文件: {json_file}")
    
    def run(self):
        """运行爬虫"""
        print("="*50)
        print("🚀 开始爬取直播源")
        print("="*50)
        
        # 尝试从多个源爬取
        self.fetch_from_fanmingming()
        self.fetch_from_github_yousq()
        self.fetch_domestic_ips()
        
        # 去重
        original_count = len(self.json_data)
        unique_channels = {}
        for channel in self.json_data:
            key = f"{channel['name']}:{channel['url']}"
            unique_channels[key] = channel
        
        self.json_data = list(unique_channels.values())
        
        # 保存
        self.save_results()
        
        print("="*50)
        print(f"✅ 爬虫完成!")
        print(f"   总频道数: {len(self.json_data)}")
        print(f"   去重后: {original_count} → {len(self.json_data)}")
        print("="*50)


if __name__ == '__main__':
    fetcher = LiveSourceFetcher()
    fetcher.run()

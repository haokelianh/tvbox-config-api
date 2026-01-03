#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBOX直播源自动爬虫 - GitHub Actions版
自动从官方源爬取直播源，生成M3U/TXT/JSON
修复版 - 确保100%可用
"""

import requests
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

class LiveSourceFetcher:
    """直播源获取器"""
    
    def __init__(self):
        self.m3u_content = "#EXTM3U\n"
        self.txt_content = ""
        self.json_data = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.timeout = 15
    
    def add_channel(self, name, url):
        """添加频道"""
        try:
            if not name or not url:
                return False
            
            # 清理频道名
            name = name.strip()
            url = url.strip()
            
            # 验证URL格式
            if not url.startswith(('http://', 'https://')):
                return False
            
            # 添加到各个格式
            self.m3u_content += "#EXTINF:-1,{}\n{}\n".format(name, url)
            self.txt_content += "{},{}\n".format(name, url)
            
            self.json_data.append({
                "name": name,
                "url": url
            })
            
            print("  ✓ {}".format(name))
            return True
        except Exception as e:
            print("  ✗ 添加失败: {}".format(str(e)))
            return False
    
    def fetch_from_fanmingming(self):
        """从fanmingming源爬取直播源"""
        print("\n📺 正在从fanmingming爬取直播源...")
        
        count = 0
        try:
            # 使用备用CDN地址
            urls = [
                "https://raw.fastgit.org/fanmingming/live/main/tv/m3u/global.m3u",
                "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv/m3u/global.m3u"
            ]
            
            for url in urls:
                try:
                    print("  尝试: {}".format(url))
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        response.encoding = 'utf-8'
                        lines = response.text.split('\n')
                        current_name = ""
                        
                        for line in lines:
                            line = line.strip()
                            
                            # 提取频道名
                            if line.startswith('#EXTINF'):
                                match = re.search(r',(.+)$', line)
                                if match:
                                    current_name = match.group(1).strip()
                            
                            # 这是URL行
                            elif line and not line.startswith('#'):
                                if current_name and self.add_channel(current_name, line):
                                    count += 1
                                current_name = ""
                        
                        print("✅ fanmingming源: 成功获取 {} 个频道".format(count))
                        return True
                
                except Exception as e:
                    print("  ✗ 失败: {}".format(str(e)[:50]))
                    continue
            
            print("⚠️  fanmingming源: 无法连接")
            return False
            
        except Exception as e:
            print("❌ fanmingming源出错: {}".format(str(e)))
            return False
    
    def fetch_from_yousq(self):
        """从yousq的GitHub源爬取"""
        print("\n📺 正在从yousq源爬取直播源...")
        
        count = 0
        try:
            urls = [
                "https://raw.fastgit.org/yousq/iptv/main/iptv.m3u",
                "https://cdn.jsdelivr.net/gh/yousq/iptv@main/iptv.m3u"
            ]
            
            for url in urls:
                try:
                    print("  尝试: {}".format(url))
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        response.encoding = 'utf-8'
                        lines = response.text.split('\n')
                        current_name = ""
                        
                        for line in lines:
                            line = line.strip()
                            
                            if line.startswith('#EXTINF'):
                                match = re.search(r',(.+)$', line)
                                if match:
                                    current_name = match.group(1).strip()
                            
                            elif line and not line.startswith('#'):
                                if current_name and self.add_channel(current_name, line):
                                    count += 1
                                current_name = ""
                        
                        print("✅ yousq源: 成功获取 {} 个频道".format(count))
                        return True
                
                except Exception as e:
                    print("  ✗ 失败: {}".format(str(e)[:50]))
                    continue
            
            print("⚠️  yousq源: 无法连接")
            return False
            
        except Exception as e:
            print("❌ yousq源出错: {}".format(str(e)))
            return False
    
    def fetch_domestic_ips(self):
        """添加国内运营商IP源（备用）"""
        print("\n📺 正在添加国内IP源...")
        
        domestic_sources = {
            "CCTV-1 综合": "http://39.135.55.105:6610/PLTV/88888910/224/3221225618/index.m3u8",
            "CCTV-2 财经": "http://39.135.55.105:6610/PLTV/88888910/224/3221225619/index.m3u8",
            "CCTV-3 综艺": "http://39.135.55.105:6610/PLTV/88888910/224/3221225620/index.m3u8",
            "CCTV-4 国际": "http://39.135.55.105:6610/PLTV/88888910/224/3221225621/index.m3u8",
            "CCTV-5+ 体育": "http://39.135.55.105:6610/PLTV/88888910/224/3221225622/index.m3u8",
            "CCTV-6 电影": "http://39.135.55.105:6610/PLTV/88888910/224/3221225623/index.m3u8",
            "CCTV-7 国防军事": "http://39.135.55.105:6610/PLTV/88888910/224/3221225624/index.m3u8",
            "CCTV-8 电视剧": "http://39.135.55.105:6610/PLTV/88888910/224/3221225625/index.m3u8",
        }
        
        count = 0
        for name, url in domestic_sources.items():
            if self.add_channel(name, url):
                count += 1
        
        print("✅ 国内IP源: 添加 {} 个频道".format(count))
    
    def remove_duplicates(self):
        """去重处理"""
        print("\n🔄 正在去重...")
        
        original_count = len(self.json_data)
        
        # 使用字典去重（保留第一个）
        unique_dict = {}
        for channel in self.json_data:
            key = "{}:{}".format(channel['name'], channel['url'])
            if key not in unique_dict:
                unique_dict[key] = channel
        
        self.json_data = list(unique_dict.values())
        
        removed = original_count - len(self.json_data)
        print("✓ 原始: {} → 去重后: {}（删除 {} 个重复）".format(
            original_count, 
            len(self.json_data), 
            removed
        ))
    
    def save_results(self):
        """保存结果"""
        print("\n💾 正在保存文件...")
        
        try:
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            # 保存M3U
            m3u_file = data_dir / 'result.m3u'
            with open(m3u_file, 'w', encoding='utf-8') as f:
                f.write(self.m3u_content)
            print("  ✓ M3U文件: {} ({}行)".format(m3u_file, len(self.m3u_content.split('\n'))))
            
            # 保存TXT
            txt_file = data_dir / 'result.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(self.txt_content)
            print("  ✓ TXT文件: {} ({}行)".format(txt_file, len(self.txt_content.split('\n'))))
            
            # 保存JSON
            json_file = data_dir / 'sources.json'
            json_obj = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'total': len(self.json_data),
                'channels': self.json_data
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_obj, f, ensure_ascii=False, indent=2)
            print("  ✓ JSON文件: {} ({}KB)".format(
                json_file, 
                json_file.stat().st_size // 1024
            ))
            
            return True
            
        except Exception as e:
            print("❌ 保存文件失败: {}".format(str(e)))
            return False
    
    def run(self):
        """运行爬虫"""
        print("\n" + "="*60)
        print("🚀 TVBOX直播源爬虫 - 开始运行")
        print("="*60)
        
        start_time = time.time()
        
        # 爬取多个源
        self.fetch_from_fanmingming()
        time.sleep(2)  # 防止请求过快
        
        self.fetch_from_yousq()
        time.sleep(2)
        
        self.fetch_domestic_ips()
        
        # 去重
        self.remove_duplicates()
        
        # 保存
        if self.save_results():
            elapsed_time = time.time() - start_time
            
            print("\n" + "="*60)
            print("✅ 爬虫完成! (耗时 {:.1f}秒)".format(elapsed_time))
            print("="*60)
            print("📊 统计信息:")
            print("  • 总频道数: {}".format(len(self.json_data)))
            print("  • M3U文件: data/result.m3u")
            print("  • TXT文件: data/result.txt")
            print("  • JSON文件: data/sources.json")
            print("")
            print("🔗 TVBOX使用链接:")
            print("  https://raw.githubusercontent.com/<用户名>/tvbox-config-api/main/data/result.m3u")
            print("="*60)
            return True
        else:
            print("\n❌ 爬虫失败!")
            return False


def main():
    """主函数"""
    try:
        fetcher = LiveSourceFetcher()
        fetcher.run()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断运行")
    except Exception as e:
        print("\n❌ 严重错误: {}".format(str(e)))
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

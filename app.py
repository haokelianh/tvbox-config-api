"""
Flask API应用 - src/api/app.py
提供REST API接口和TVBOX配置
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import logging
from datetime import datetime
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # CORS支持
    CORS(app)
    
    # ============ API 路由 ============
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }), 200
    
    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取TVBOX配置"""
        try:
            config = {
                "version": "2.0",
                "spider": "jar;md5;https://example.com/spider.jar",
                "wallpaper": "https://example.com/wallpaper.jpg",
                "lives": [{
                    "group": "自定义直播",
                    "channels": [{
                        "name": "自动聚合源",
                        "urls": [{
                            "name": "M3U格式",
                            "url": f"{request.host_url.rstrip('/')}/api/sources/m3u"
                        }]
                    }]
                }]
            }
            return jsonify({'status': 'success', 'data': config, 'timestamp': datetime.now().isoformat()}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sources', methods=['GET'])
    def get_sources():
        """获取所有直播源"""
        try:
            sources_file = Path('data') / 'sources.json'
            if not sources_file.exists():
                return jsonify({'status': 'error', 'message': '直播源数据不可用'}), 503
            
            with open(sources_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            
            channels = data.get('channels', [])
            total = len(channels)
            start = (page - 1) * per_page
            end = start + per_page
            
            return jsonify({
                'status': 'success',
                'data': {
                    'channels': channels[start:end],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                },
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sources/m3u', methods=['GET'])
    def get_m3u_sources():
        """获取M3U格式的直播源"""
        try:
            m3u_file = Path('data') / 'result.m3u'
            if not m3u_file.exists():
                return jsonify({'status': 'error', 'message': 'M3U文件不可用'}), 503
            
            if request.args.get('download') == '1':
                return send_file(m3u_file, mimetype='application/x-mpegURL', as_attachment=True)
            
            with open(m3u_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'application/x-mpegURL; charset=utf-8'}
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sources/txt', methods=['GET'])
    def get_txt_sources():
        """获取TXT格式的直播源"""
        try:
            txt_file = Path('data') / 'result.txt'
            if not txt_file.exists():
                return jsonify({'status': 'error', 'message': 'TXT文件不可用'}), 503
            
            if request.args.get('download') == '1':
                return send_file(txt_file, mimetype='text/plain', as_attachment=True)
            
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sources/search', methods=['GET'])
    def search_sources():
        """搜索直播源"""
        try:
            query = request.args.get('q', '').lower()
            limit = request.args.get('limit', 20, type=int)
            
            if not query:
                return jsonify({'status': 'error', 'message': '搜索关键字不能为空'}), 400
            
            sources_file = Path('data') / 'sources.json'
            if not sources_file.exists():
                return jsonify({'status': 'error', 'message': '直播源数据不可用'}), 503
            
            with open(sources_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = []
            for channel in data.get('channels', []):
                if query in channel['name'].lower():
                    results.append(channel)
                    if len(results) >= limit:
                        break
            
            return jsonify({
                'status': 'success',
                'data': {'query': query, 'results': results, 'count': len(results)},
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """获取统计信息"""
        try:
            sources_file = Path('data') / 'sources.json'
            
            stats = {
                'total_channels': 0,
                'validated_channels': 0,
                'source_files': [],
                'last_update': None,
            }
            
            if sources_file.exists():
                with open(sources_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                channels = data.get('channels', [])
                stats['total_channels'] = len(channels)
                stats['validated_channels'] = sum(1 for ch in channels if ch.get('validated', False))
                stats['last_update'] = data.get('timestamp')
            
            for file_type in ['m3u', 'txt']:
                file_path = Path('data') / f'result.{file_type}'
                if file_path.exists():
                    stats['source_files'].append({
                        'type': file_type,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
            
            return jsonify({
                'status': 'success',
                'data': stats,
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'message': '资源不存在', 'code': 404}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'status': 'error', 'message': '内部服务器错误', 'code': 500}), 500
    
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)

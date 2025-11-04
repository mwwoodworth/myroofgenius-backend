#!/usr/bin/env python3
import json
import psycopg2
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': 'Brain0ps2O2S'
}

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Gather metrics
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM customers) as customers,
                    (SELECT COUNT(*) FROM jobs) as jobs,
                    (SELECT COUNT(*) FROM invoices) as invoices,
                    (SELECT COUNT(*) FROM ai_agents WHERE status = 'active') as active_agents,
                    (SELECT COUNT(*) FROM centerpoint_sync_log WHERE started_at > NOW() - INTERVAL '1 hour') as recent_syncs
            ''')
            
            metrics = cursor.fetchone()
            
            response = {
                'timestamp': datetime.now().isoformat(),
                'customers': metrics[0],
                'jobs': metrics[1],
                'invoices': metrics[2],
                'active_ai_agents': metrics[3],
                'recent_syncs': metrics[4],
                'status': 'operational'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
            cursor.close()
            conn.close()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MetricsHandler)
    print('Metrics dashboard running on port 8080...')
    server.serve_forever()

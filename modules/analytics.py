from datetime import datetime, timedelta
from typing import Dict, List, Any

class Analytics:
    def __init__(self, db):
        self.db = db

    def get_employee_statistics(self) -> Dict[str, Any]:
        """
        获取员工统计信息
        迁移自 employee.py 的 get_employee_statistics 方法
        """
        try:
            total = 0
            active = 0
            terminated = 0

            total_res = self.db.execute_query("SELECT COUNT(*) as total FROM employees")
            if total_res:
                total = total_res[0]['total']

            active_res = self.db.execute_query("SELECT COUNT(*) as active FROM employees WHERE status = '在职'")
            if active_res:
                active = active_res[0]['active']

            term_res = self.db.execute_query("SELECT COUNT(*) as terminated FROM employees WHERE status = '离职'")
            if term_res:
                terminated = term_res[0]['terminated']

            active_rate = (active / total * 100) if total > 0 else 0

            dept_sql = '''
                       SELECT d.department_name, COUNT(e.employee_id) as count
                       FROM departments d
                           LEFT JOIN employees e
                       ON d.department_id = e.department_id AND e.status = '在职'
                       GROUP BY d.department_id
                       ORDER BY count DESC
                       '''
            by_dept = self.db.execute_query(dept_sql)

            return {
                'success': True,
                'data': {
                    'total': total,
                    'active': active,
                    'terminated': terminated,
                    'active_rate': round(active_rate, 2),
                    'by_department': by_dept or []
                },
                'message': f'员工统计完成，共{total}名员工'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'员工统计失败: {str(e)}',
                'data': {'total': 0, 'active': 0, 'terminated': 0, 'active_rate': 0, 'by_department': []}
            }

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        获取订单统计信息
        迁移自 orders.py 的 get_order_statistics 方法
        """
        try:
            total_res = self.db.execute_query("SELECT COUNT(*) as total FROM orders")
            total = total_res[0]['total'] if total_res else 0

            status_sql = '''
                         SELECT order_status, COUNT(*) as count
                         FROM orders
                         GROUP BY order_status
                         '''
            by_status = self.db.execute_query(status_sql) or []

            payment_sql = '''
                          SELECT payment_status, COUNT(*) as count
                          FROM orders
                          GROUP BY payment_status
                          '''
            by_payment = self.db.execute_query(payment_sql) or []
            print("订单状态统计 by_status:", by_status)

            today = datetime.now().strftime('%Y-%m-%d')
            today_sql = '''
                        SELECT COUNT(*)                                                 as today_total, \
                               SUM(CASE WHEN order_status = '预定中' THEN 1 ELSE 0 END) as today_reserved, \
                               SUM(CASE WHEN order_status = '已入住' THEN 1 ELSE 0 END) as today_checked_in, \
                               SUM(CASE WHEN order_status = '已完成' THEN 1 ELSE 0 END) as today_completed, \
                               SUM(total_amount)                                        as today_total_amount, \
                               SUM(paid_amount)                                         as today_paid_amount
                        FROM orders
                        WHERE DATE (created_at) = DATE (?)
                        '''
            today_stats_result = self.db.execute_query(today_sql, (today,))
            today_stats = today_stats_result[0] if today_stats_result else {
                'today_total': 0,
                'today_reserved': 0,
                'today_checked_in': 0,
                'today_completed': 0,
                'today_total_amount': 0,
                'today_paid_amount': 0
            }

            trend_sql = '''
                        SELECT
                            DATE (created_at) as date, COUNT (*) as count, SUM (total_amount) as total_amount
                        FROM orders
                        WHERE created_at >= DATE ('now', '-7 days')
                        GROUP BY DATE (created_at)
                        ORDER BY date
                        '''
            trend_data = self.db.execute_query(trend_sql) or []

            # 计算支付率
            payment_rate = 0
            if today_stats.get('today_total_amount', 0) > 0:
                payment_rate = (today_stats.get('today_paid_amount', 0) /
                                today_stats.get('today_total_amount', 0) * 100)

            return {
                'success': True,
                'data': {
                    'total': total,
                    'by_status': by_status,
                    'by_payment': by_payment,
                    'today_stats': today_stats,
                    'trend_data': trend_data,
                    'payment_rate': round(payment_rate, 2)
                },
                'message': f'订单统计完成，共{total}个订单'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'订单统计失败: {str(e)}',
                'data': {}
            }

    def get_customer_statistics(self) -> Dict[str, Any]:
        """
        获取客户统计信息
        """
        try:
            # 客户总数
            total_res = self.db.execute_query("SELECT COUNT(*) as total FROM customers")
            total = total_res[0]['total'] if total_res else 0

            # 今日新增客户
            today = datetime.now().strftime('%Y-%m-%d')
            today_sql = """
                        SELECT COUNT(*) as today_new
                        FROM customers
                        WHERE DATE (created_at) = DATE (?) \
                        """
            today_result = self.db.execute_query(today_sql, (today,))
            today_new = today_result[0]['today_new'] if today_result else 0

            # 近7天新增客户趋势
            trend_sql = """
                        SELECT
                            DATE (created_at) as date, COUNT (*) as count
                        FROM customers
                        WHERE created_at >= DATE ('now', '-7 days')
                        GROUP BY DATE (created_at)
                        ORDER BY date
                        """
            trend_data = self.db.execute_query(trend_sql) or []

            # 客户订单统计
            order_sql = """
                        SELECT c.id, \
                               c.name, \
                               COUNT(o.order_id)   as order_count, \
                               SUM(o.total_amount) as total_spent
                        FROM customers c
                                 LEFT JOIN orders o ON c.id = o.customer_id
                        GROUP BY c.id
                        HAVING order_count > 0
                        ORDER BY total_spent DESC LIMIT 10
                        """
            top_customers = self.db.execute_query(order_sql) or []

            return {
                'success': True,
                'data': {
                    'total': total,
                    'today_new': today_new,
                    'trend_data': trend_data,
                    'top_customers': top_customers
                },
                'message': f'客户统计完成，共{total}名客户'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'客户统计失败: {str(e)}',
                'data': {}
            }

    def get_room_statistics(self, stat_date: str = None):
        """
        获取房间统计信息
        """
        print("stat_date =", stat_date)

        if not stat_date:
            stat_date = datetime.now().strftime('%Y-%m-%d')
        
        # 统一日期格式为 YYYY-MM-DD
        stat_date_clean = stat_date.replace('/', '-')
        
        try:
            # 房间总数及各状态统计
            status_sql = """
                        SELECT status, \
                                COUNT(*) as count,
                            ROUND(AVG(price), 2) as avg_price
                        FROM rooms
                        GROUP BY status \
                        """
            status_stats = self.db.execute_query(status_sql) or []

            # 房型统计
            type_sql = """
                    SELECT room_type, \
                            COUNT(*) as count,
                        ROUND(AVG(price), 2) as avg_price,
                        ROUND(AVG(area), 2) as avg_area
                    FROM rooms
                    GROUP BY room_type
                    ORDER BY count DESC \
                    """
            type_stats = self.db.execute_query(type_sql) or []

            # 价格区间统计
            price_sql = """
                        SELECT CASE \
                                WHEN price < 200 THEN '经济型 (<200)' \
                                WHEN price BETWEEN 200 AND 400 THEN '舒适型 (200-400)' \
                                WHEN price > 400 THEN '豪华型 (>400)' \
                                END as price_range, \
                            COUNT(*) as count
                        FROM rooms
                        GROUP BY price_range
                        ORDER BY price_range \
                        """
            price_stats = self.db.execute_query(price_sql) or []

            # 房间总数
            total_res = self.db.execute_query("SELECT COUNT(*) as total FROM rooms")
            total = total_res[0]['total'] if total_res else 0

            # 查看所有当前有效的订单
            debug_sql = """
                    SELECT 
                        order_id,
                        room_number,
                        check_in_date,
                        check_out_date,
                        order_status,
                        DATE(check_in_date) as check_in_date_parsed,
                        DATE(check_out_date) as check_out_date_parsed
                    FROM orders
                    WHERE order_status IN ('预定中', '已入住')
                    """
            debug_result = self.db.execute_query(debug_sql) or []
            print("=== 调试信息 - 当前有效订单 ===")
            print(f"找到 {len(debug_result)} 个有效订单")
            for order in debug_result:
                print(f"订单 {order['order_id']}: 房间 {order['room_number']}, "
                    f"入住 {order['check_in_date']} -> 退房 {order['check_out_date']}, "
                    f"状态: {order['order_status']}")
                print(f"  解析后入住: {order.get('check_in_date_parsed')}, "
                    f"解析后退房: {order.get('check_out_date_parsed')}")
            print("=== 调试信息结束 ===\n")

            #测试统计日期的解析
            test_date_sql = """
                        SELECT DATE(?) as test_date_parsed,
                                DATE('now') as current_date
                        """
            test_date_res = self.db.execute_query(test_date_sql, (stat_date_clean,))
            print(f"测试日期解析: 输入={stat_date_clean}, 解析结果={test_date_res}")

            #详细的入住率查询（带更多信息）
            detailed_occupied_sql = """
                                SELECT 
                                    o.order_id,
                                    o.room_number,
                                    o.check_in_date,
                                    o.check_out_date,
                                    o.order_status,
                                    DATE(o.check_in_date) as ci_parsed,
                                    DATE(o.check_out_date) as co_parsed,
                                    DATE(?) as stat_date_parsed,
                                    CASE 
                                        WHEN DATE(?) >= DATE(o.check_in_date) 
                                            AND DATE(?) < DATE(o.check_out_date)
                                        THEN 1 
                                        ELSE 0 
                                    END as is_occupied
                                FROM orders o
                                WHERE o.order_status IN ('预定中', '已入住')
                                ORDER BY o.order_id
                                """
            detailed_res = self.db.execute_query(
                detailed_occupied_sql,
                (stat_date_clean, stat_date_clean, stat_date_clean)
            )
            
            print(f"\n=== 详细的入住判断 ===")
            print(f"统计日期: {stat_date_clean}")
            if detailed_res:
                for row in detailed_res:
                    print(f"订单 {row['order_id']}: 房间 {row['room_number']}")
                    print(f"  原始: 入住 {row['check_in_date']} -> 退房 {row['check_out_date']}")
                    print(f"  解析: 入住 {row['ci_parsed']} -> 退房 {row['co_parsed']}")
                    print(f"  统计日期解析: {row['stat_date_parsed']}")
                    print(f"  是否入住: {row['is_occupied']}")
                    
                    # 额外的日期比较逻辑
                    try:
                        # 尝试手动比较
                        check_in = str(row['check_in_date'])
                        check_out = str(row['check_out_date'])
                        stat_date_str = stat_date_clean
                        
                        print(f"  手动比较: {stat_date_str} >= {check_in} and < {check_out}")
                        print(f"  比较结果: {'是' if stat_date_str >= check_in and stat_date_str < check_out else '否'}")
                    except Exception as e:
                        print(f"  手动比较错误: {e}")
                    print()
            
            #计算入住率
            occupied_sql = """
                        SELECT COUNT(DISTINCT room_number) as occupied_count
                        FROM orders
                        WHERE order_status IN ('预定中', '已入住')
                        AND DATE(?) >= DATE(check_in_date)
                        AND DATE(?) < DATE(check_out_date)
                        """
            
            occupied_res = self.db.execute_query(
                occupied_sql,
                (stat_date_clean, stat_date_clean)
            )
            
            print(f"\n=== 入住率计算结果 ===")
            print(f"查询结果: {occupied_res}")
            
            occupied = occupied_res[0]['occupied_count'] if occupied_res else 0
            occupancy_rate = (occupied / total * 100) if total > 0 else 0
            
            print(f"入住房间数: {occupied}, 总房间数: {total}, 入住率: {occupancy_rate}%")
            
            # 尝试其他查询方法
            if occupied == 0:
                print("\n=== 尝试其他查询方法 ===")
                
                # 方法A：使用字符串比较
                alt_sql_a = """
                        SELECT COUNT(DISTINCT room_number) as occupied_count
                        FROM orders
                        WHERE order_status IN ('预定中', '已入住')
                        AND ? >= check_in_date
                        AND ? < check_out_date
                        """
                alt_res_a = self.db.execute_query(alt_sql_a, (stat_date_clean, stat_date_clean))
                print(f"方法A（字符串比较）结果: {alt_res_a}")
                
                # 方法B：只检查 check_in_date 等于统计日期的情况
                alt_sql_b = """
                        SELECT COUNT(DISTINCT room_number) as occupied_count
                        FROM orders
                        WHERE order_status IN ('预定中', '已入住')
                        AND DATE(check_in_date) = DATE(?)
                        """
                alt_res_b = self.db.execute_query(alt_sql_b, (stat_date_clean,))
                print(f"方法B（入住日期等于统计日期）结果: {alt_res_b}")
                
                # 方法C：查看今天的所有订单
                today_sql = """
                        SELECT room_number, check_in_date, check_out_date, order_status
                        FROM orders
                        WHERE DATE(check_in_date) <= DATE('now')
                        AND DATE(check_out_date) >= DATE('now')
                        AND order_status IN ('预定中', '已入住')
                        """
                today_res = self.db.execute_query(today_sql)
                print(f"今天（当前日期）的有效订单: {today_res}")

            return {
                'success': True,
                'data': {
                    'total': total,
                    'occupied': occupied,
                    'occupancy_rate': round(occupancy_rate, 2),
                    'status_stats': status_stats,
                    'type_stats': type_stats,
                    'price_stats': price_stats
                },
                'message': f'房间统计完成，共{total}间房间，入住率{round(occupancy_rate, 2)}%'
            }
        except Exception as e:
            print(f"房间统计异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'房间统计失败: {str(e)}',
                'data': {}
            }
        
    def get_revenue_analysis(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        获取收入分析

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        try:
            # 设置默认日期范围（最近30天）
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            # 总收入统计
            revenue_sql = """
                          SELECT SUM(total_amount) as total_revenue, \
                                 SUM(paid_amount)  as total_paid, \
                                 COUNT(*)          as order_count
                          FROM orders
                          WHERE DATE (created_at) BETWEEN DATE (?) AND DATE (?) \
                          """
            revenue_res = self.db.execute_query(revenue_sql, (start_date, end_date))
            revenue_stats = revenue_res[0] if revenue_res else {
                'total_revenue': 0,
                'total_paid': 0,
                'order_count': 0
            }

            # 每日收入趋势
            daily_sql = """
                        SELECT
                            DATE (created_at) as date, SUM (total_amount) as daily_revenue, SUM (paid_amount) as daily_paid, COUNT (*) as daily_orders
                        FROM orders
                        WHERE DATE (created_at) BETWEEN DATE (?) AND DATE (?)
                        GROUP BY DATE (created_at)
                        ORDER BY date \
                        """
            daily_trend = self.db.execute_query(daily_sql, (start_date, end_date)) or []

            # 房型收入分析
            room_type_sql = """
                            SELECT r.room_type, \
                                   SUM(o.total_amount)           as revenue, \
                                   COUNT(o.order_id)             as order_count, \
                                   ROUND(AVG(o.total_amount), 2) as avg_order_value
                            FROM orders o
                                     JOIN rooms r ON o.room_number = r.room_number
                            WHERE DATE (o.created_at) BETWEEN DATE (?) AND DATE (?)
                            GROUP BY r.room_type
                            ORDER BY revenue DESC \
                            """
            room_type_stats = self.db.execute_query(room_type_sql, (start_date, end_date)) or []

            # 支付方式统计
            payment_sql = """
                          SELECT payment_status, \
                                 SUM(total_amount) as amount, \
                                 COUNT(*) as count
                          FROM orders
                          WHERE DATE (created_at) BETWEEN DATE (?) AND DATE (?)
                          GROUP BY payment_status \
                          """
            payment_stats = self.db.execute_query(payment_sql, (start_date, end_date)) or []

            return {
                'success': True,
                'data': {
                    'period': {'start': start_date, 'end': end_date},
                    'revenue_stats': revenue_stats,
                    'daily_trend': daily_trend,
                    'room_type_stats': room_type_stats,
                    'payment_stats': payment_stats
                },
                'message': f'收入分析完成 ({start_date} 至 {end_date})'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'收入分析失败: {str(e)}',
                'data': {}
            }

    def get_dashboard_summary(self, stat_date: str = None) -> Dict[str, Any]:
        """
        获取仪表板汇总数据（基于指定日期）
        """
        try:
            # 统一统计日期
            if not stat_date:
                stat_date = datetime.now().strftime('%Y/%m/%d')

            # 各模块统计
            employee_stats = self.get_employee_statistics()
            order_stats = self.get_order_statistics()
            customer_stats = self.get_customer_statistics()
            room_stats = self.get_room_statistics(stat_date)

            # 指定日期收入
            revenue_sql = """
                SELECT
                    COUNT(*) as total_orders,
                    SUM(CASE WHEN order_status = '预定中' THEN 1 ELSE 0 END) as reserved,
                    SUM(CASE WHEN order_status = '已入住' THEN 1 ELSE 0 END) as checked_in,
                    SUM(CASE WHEN order_status = '已完成' THEN 1 ELSE 0 END) as completed,
                    SUM(total_amount) as total_amount,
                    SUM(paid_amount) as paid_amount
                FROM orders
                WHERE DATE(REPLACE(created_at, '/', '-')) = DATE(REPLACE(?, '/', '-'))
            """

            revenue_res = self.db.execute_query(revenue_sql, (stat_date,))
            revenue = revenue_res[0] if revenue_res else {
                'total_orders': 0,
                'reserved': 0,
                'checked_in': 0,
                'completed': 0,
                'total_amount': 0,
                'paid_amount': 0
            }

            # 最近 7 天趋势
            week_trend_sql = """
                SELECT
                    DATE(REPLACE(created_at, '/', '-')) as date,
                    COUNT(*) as orders,
                    SUM(total_amount) as revenue
                FROM orders
                WHERE DATE(REPLACE(created_at, '/', '-')) >= DATE('now', '-6 days')
                GROUP BY DATE(REPLACE(created_at, '/', '-'))
                ORDER BY date
            """
            week_trend = self.db.execute_query(week_trend_sql) or []

            summary = {
                'stat_date': stat_date,
                'employees': employee_stats['data']['total'] if employee_stats['success'] else 0,
                'active_employees': employee_stats['data']['active'] if employee_stats['success'] else 0,
                'customers': customer_stats['data']['total'] if customer_stats['success'] else 0,
                'rooms': room_stats['data']['total'] if room_stats['success'] else 0,
                'occupied_rooms': room_stats['data']['occupied'] if room_stats['success'] else 0,
                'occupancy_rate': room_stats['data']['occupancy_rate'] if room_stats['success'] else 0,
                'total_orders': order_stats['data']['total'] if order_stats['success'] else 0,
                'revenue': revenue
            }

            return {
                'success': True,
                'data': {
                    'summary': summary,
                    'week_trend': week_trend,
                    'employee_stats': employee_stats['data'] if employee_stats['success'] else {},
                    'order_stats': order_stats['data'] if order_stats['success'] else {},
                    'customer_stats': customer_stats['data'] if customer_stats['success'] else {},
                    'room_stats': room_stats['data'] if room_stats['success'] else {}
                },
                'message': f'{stat_date} 仪表板数据加载完成'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'仪表板数据加载失败: {str(e)}',
                'data': {}
            }



    def generate_chart_data(self, chart_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成图表数据

        Args:
            chart_type: 图表类型 ('employee_dept', 'order_status', 'room_type', 'revenue_trend', 'customer_trend')
            params: 额外参数
        """
        try:
            chart_data = {
                'labels': [],
                'datasets': [],
                'success': True
            }

            if chart_type == 'employee_dept':
                # 员工部门分布图
                stats = self.get_employee_statistics()
                if stats['success']:
                    by_dept = stats['data']['by_department']
                    chart_data['labels'] = [dept['department_name'] for dept in by_dept]
                    chart_data['datasets'] = [{
                        'label': '员工人数',
                        'data': [dept['count'] for dept in by_dept],
                        'backgroundColor': self._generate_colors(len(by_dept))
                    }]

            elif chart_type == 'order_status':
                # 订单状态分布图
                print("订单状态统计:", stats)

                stats = self.get_order_statistics()
                if stats['success']:
                    by_status = stats['data']['by_status']
                    chart_data['labels'] = [status['order_status'] for status in by_status]
                    chart_data['datasets'] = [{
                        'label': '订单数量',
                        'data': [status['count'] for status in by_status],
                        'backgroundColor': self._generate_colors(len(by_status))
                    }]

            elif chart_type == 'room_type':
                # 房型分布图
                stats = self.get_room_statistics()
                if stats['success']:
                    by_type = stats['data']['type_stats']
                    chart_data['labels'] = [room_type['room_type'] for room_type in by_type]
                    chart_data['datasets'] = [{
                        'label': '房间数量',
                        'data': [room_type['count'] for room_type in by_type],
                        'backgroundColor': self._generate_colors(len(by_type))
                    }]

            elif chart_type == 'revenue_trend':
                # 收入趋势图
                start_date = params.get('start_date') if params else None
                end_date = params.get('end_date') if params else None
                stats = self.get_revenue_analysis(start_date, end_date)
                if stats['success']:
                    daily_trend = stats['data']['daily_trend']
                    chart_data['labels'] = [day['date'] for day in daily_trend]
                    chart_data['datasets'] = [
                        {
                            'label': '每日收入',
                            'data': [day['daily_revenue'] for day in daily_trend],
                            'borderColor': '#4CAF50',
                            'backgroundColor': 'rgba(76, 175, 80, 0.2)',
                            'fill': True
                        }
                    ]

            elif chart_type == 'customer_trend':
                # 客户增长趋势图
                stats = self.get_customer_statistics()
                if stats['success']:
                    trend_data = stats['data']['trend_data']
                    chart_data['labels'] = [day['date'] for day in trend_data]
                    chart_data['datasets'] = [{
                        'label': '新增客户',
                        'data': [day['count'] for day in trend_data],
                        'borderColor': '#2196F3',
                        'backgroundColor': 'rgba(33, 150, 243, 0.2)',
                        'fill': True
                    }]

            else:
                return {
                    'success': False,
                    'message': f'不支持的图表类型: {chart_type}'
                }

            return chart_data

        except Exception as e:
            return {
                'success': False,
                'message': f'图表数据生成失败: {str(e)}'
            }

    def _generate_colors(self, count: int) -> List[str]:
        """生成颜色数组"""
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#8AC926', '#1982C4',
            '#6A4C93', '#F15BB5', '#00BBF9', '#00F5D4'
        ]
        return colors[:count] if count <= len(colors) else colors * (count // len(colors) + 1)[:count]

    def export_statistics(self, export_type: str = 'json') -> Dict[str, Any]:
        """
        导出统计数据

        Args:
            export_type: 导出类型 ('json', 'summary')
        """
        try:
            # 收集所有统计数据
            dashboard_data = self.get_dashboard_summary()

            if export_type == 'json':
                # 返回完整JSON数据
                export_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                export_data = {
                    'export_time': export_time,
                    'data': dashboard_data['data'] if dashboard_data['success'] else {},
                    'success': True
                }

                return {
                    'success': True,
                    'data': export_data,
                    'format': 'json',
                    'message': '统计数据导出完成'
                }

            elif export_type == 'summary':
                # 生成文本摘要
                summary = dashboard_data['data']['summary'] if dashboard_data['success'] else {}

                text_summary = f"""
                ===== 酒店管理系统统计报告 =====
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                1. 员工统计
                --------------------------------
                员工总数: {summary.get('employees', 0)} 人
                在职员工: {summary.get('active_employees', 0)} 人

                2. 客户统计
                --------------------------------
                客户总数: {summary.get('customers', 0)} 人
                今日新增: {summary.get('today_new_customers', 0)} 人

                3. 房间统计
                --------------------------------
                房间总数: {summary.get('rooms', 0)} 间
                已入住: {summary.get('occupied_rooms', 0)} 间
                入住率: {summary.get('occupancy_rate', 0)}%

                4. 订单与收入
                --------------------------------
                订单总数: {summary.get('total_orders', 0)} 个
                今日收入: ¥{summary.get('today_revenue', 0):.2f}
                今日实收: ¥{summary.get('today_paid', 0):.2f}

                ================================
                """

                return {
                    'success': True,
                    'data': text_summary,
                    'format': 'text',
                    'message': '统计摘要生成完成'
                }

            else:
                return {
                    'success': False,
                    'message': f'不支持的导出类型: {export_type}'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'统计数据导出失败: {str(e)}'
            }
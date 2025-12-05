from datetime import datetime

class Orders:
    def __init__(self, db):
        self.db = db

    def generate_order_id(self):
        date_part = datetime.now().strftime('%y%m%d')

        sql = """
              SELECT MAX(order_id) as max_id
              FROM orders
              WHERE order_id LIKE ?
              """
        result = self.db.execute_query(sql, (f"{date_part}%",))

        if result and result[0]['max_id']:
            max_id = result[0]['max_id']
            last_serial = int(max_id[-3:])
            new_serial = last_serial + 1
        else:
            new_serial = 1

        return f"{date_part}{str(new_serial).zfill(3)}"

    def create_order(self, input_data: dict) -> dict:
        """
        创建新订单

        Args:
            input_data: 订单数据字典，包含customer_id, room_number, check_in_date, check_out_date等

        Returns:
            dict: 包含success, data, message的返回结果
        """
        try:
            required_fields = ['customer_id', 'room_number', 'check_in_date', 'check_out_date']
            for field in required_fields:
                if not input_data.get(field):
                    return {
                        'success': False,
                        'message': f'{field}是必填项'
                    }

            valid_statuses = ['预定中', '已入住', '已完成', '已取消', '异常']
            if input_data.get('order_status') and input_data['order_status'] not in valid_statuses:
                return {
                    'success': False,
                    'message': f'订单状态必须是: {", ".join(valid_statuses)}'
                }

            valid_payment_statuses = ['未支付', '部分支付', '已支付', '已退款']
            if input_data.get('payment_status') and input_data['payment_status'] not in valid_payment_statuses:
                return {
                    'success': False,
                    'message': f'支付状态必须是: {", ".join(valid_payment_statuses)}'
                }

            order_id = self.generate_order_id()

            try:
                check_in = datetime.strptime(input_data['check_in_date'], '%Y-%m-%d')
                check_out = datetime.strptime(input_data['check_out_date'], '%Y-%m-%d')
                days = (check_out - check_in).days
                if days <= 0:
                    return {
                        'success': False,
                        'message': '退房日期必须晚于入住日期'
                    }
            except ValueError:
                return {
                    'success': False,
                    'message': '日期格式错误，请使用YYYY-MM-DD格式'
                }

            db_data = {
                'order_id': order_id,
                'customer_id': input_data['customer_id'],
                'room_number': input_data['room_number'].strip(),
                'check_in_date': input_data['check_in_date'],
                'check_out_date': input_data['check_out_date'],
                'days': days
            }

            if input_data.get('total_amount'):
                try:
                    db_data['total_amount'] = float(input_data['total_amount'])
                except:
                    return {
                        'success': False,
                        'message': '总金额格式错误'
                    }
            else:
                room_sql = "SELECT price FROM rooms WHERE room_number = ?"
                room_result = self.db.execute_query(room_sql, (input_data['room_number'],))
                if room_result and room_result[0]['price']:
                    room_price = room_result[0]['price']
                    db_data['total_amount'] = room_price * days
                else:
                    db_data['total_amount'] = 0.00

            optional_fields = ['employee_id', 'payment_status', 'order_status', 'special_requests']

            for field in optional_fields:
                if input_data.get(field):
                    db_data[field] = input_data[field].strip() if isinstance(input_data[field], str) else input_data[
                        field]

            if input_data.get('paid_amount'):
                try:
                    db_data['paid_amount'] = float(input_data['paid_amount'])
                except:
                    db_data['paid_amount'] = 0.00

            if self._insert_order(db_data):
                order_info = self._get_order_by_id(order_id)
                return {
                    'success': True,
                    'data': order_info,
                    'message': f'订单创建成功，订单号：{order_id}'
                }
            else:
                return {
                    'success': False,
                    'message': '创建失败'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'创建过程中发生错误：{str(e)}'
            }

    def update_order(self, order_id: str, update_data: dict) -> dict:
        """
        更新订单信息

        Args:
            order_id: 订单ID
            update_data: 要更新的字段字典

        Returns:
            dict: 包含success, message的返回结果
        """
        try:
            existing = self._get_order_by_id(order_id)
            if not existing:
                return {
                    'success': False,
                    'message': '订单不存在'
                }

            if 'order_status' in update_data:
                valid_statuses = ['预定中', '已入住', '已完成', '已取消', '异常']
                if update_data['order_status'] not in valid_statuses:
                    return {
                        'success': False,
                        'message': f'订单状态必须是: {", ".join(valid_statuses)}'
                    }

            if self._db_update_order(order_id, update_data):
                return {
                    'success': True,
                    'message': '订单信息更新成功'
                }
            else:
                return {
                    'success': False,
                    'message': '更新失败'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'更新订单失败: {str(e)}'
            }

    def delete_order(self, order_id: str) -> dict:
        """
        删除订单

        Args:
            order_id: 订单ID

        Returns:
            dict: 包含success, message的返回结果
        """
        try:
            if self._db_delete_order(order_id):
                return {
                    'success': True,
                    'message': '订单删除成功'
                }
            else:
                return {
                    'success': False,
                    'message': '订单不存在或删除失败'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除订单失败: {str(e)}'
            }

    def get_order(self, order_id: str) -> dict:
        """
        获取单个订单信息

        Args:
            order_id: 订单ID

        Returns:
            dict: 包含success, data, message的返回结果
        """
        order = self._get_order_by_id(order_id)
        if order:
            return {
                'success': True,
                'data': order
            }
        else:
            return {
                'success': False,
                'message': '订单不存在'
            }

    def get_all_orders(self) -> dict:
        """
        获取所有订单

        Returns:
            dict: 包含success, data, message的返回结果
        """
        sql = '''
              SELECT o.*,
                     c.name  as customer_name,
                     c.phone as customer_phone,
                     r.room_type,
                     e.employee_name
              FROM orders o
                       LEFT JOIN customers c ON o.customer_id = c.id
                       LEFT JOIN rooms r ON o.room_number = r.room_number
                       LEFT JOIN employees e ON o.employee_id = e.employee_id
              ORDER BY o.created_at DESC
              '''
        orders = self.db.execute_query(sql)
        return {
            'success': True,
            'data': orders or [],
            'message': f'获取到{len(orders) if orders else 0}个订单'
        }

    def get_orders_by_date(self, date: str) -> dict:
        """
        获取某日期的所有订单

        Args:
            date: 日期字符串，格式YYYY-MM-DD

        Returns:
            dict: 包含success, data, message的返回结果
        """
        sql = '''
              SELECT o.*,
                     c.name as customer_name,
                     r.room_type,
                     e.employee_name
              FROM orders o
                       LEFT JOIN customers c ON o.customer_id = c.id
                       LEFT JOIN rooms r ON o.room_number = r.room_number
                       LEFT JOIN employees e ON o.employee_id = e.employee_id
              WHERE DATE (o.created_at) = DATE (?)
              ORDER BY o.created_at DESC
              '''
        orders = self.db.execute_query(sql, (date,))
        return {
            'success': True,
            'data': orders or [],
            'message': f'{date}共有{len(orders) if orders else 0}个订单'
        }

    def get_orders_by_customer(self, customer_id: int) -> dict:
        """
        获取客户的所有订单

        Args:
            customer_id: 客户ID

        Returns:
            dict: 包含success, data, message的返回结果
        """
        sql = '''
              SELECT o.*,
                     r.room_type,
                     e.employee_name
              FROM orders o
                       LEFT JOIN rooms r ON o.room_number = r.room_number
                       LEFT JOIN employees e ON o.employee_id = e.employee_id
              WHERE o.customer_id = ?
              ORDER BY o.check_in_date DESC
              '''
        orders = self.db.execute_query(sql, (customer_id,))
        return {
            'success': True,
            'data': orders or [],
            'message': f'客户{customer_id}共有{len(orders) if orders else 0}个订单'
        }

    def get_orders_by_room(self, room_number: str, start_date: str = None, end_date: str = None) -> dict:
        """
        获取房间的订单记录

        Args:
            room_number: 房间号
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            dict: 包含success, data, message的返回结果
        """
        params = [room_number]
        where_clause = "WHERE o.room_number = ?"

        if start_date:
            where_clause += " AND o.check_in_date >= ?"
            params.append(start_date)
        if end_date:
            where_clause += " AND o.check_out_date <= ?"
            params.append(end_date)

        sql = f'''
            SELECT o.*, 
                   c.name as customer_name,
                   e.employee_name
            FROM orders o
            LEFT JOIN customers c ON o.customer_id = c.id
            LEFT JOIN employees e ON o.employee_id = e.employee_id
            {where_clause}
            ORDER BY o.check_in_date DESC
        '''
        orders = self.db.execute_query(sql, tuple(params))
        return {
            'success': True,
            'data': orders or [],
            'message': f'房间{room_number}共有{len(orders) if orders else 0}个订单'
        }

    def get_orders_by_status(self, status: str) -> dict:
        """
        根据状态筛选订单

        Args:
            status: 订单状态

        Returns:
            dict: 包含success, data, message的返回结果
        """
        sql = '''
              SELECT o.*,
                     c.name as customer_name,
                     r.room_type,
                     e.employee_name
              FROM orders o
                       LEFT JOIN customers c ON o.customer_id = c.id
                       LEFT JOIN rooms r ON o.room_number = r.room_number
                       LEFT JOIN employees e ON o.employee_id = e.employee_id
              WHERE o.order_status = ?
              ORDER BY o.check_in_date
              '''
        orders = self.db.execute_query(sql, (status,))
        return {
            'success': True,
            'data': orders or [],
            'message': f'{status}状态共有{len(orders) if orders else 0}个订单'
        }

    def get_order_statistics(self) -> dict:
        """
        获取订单统计信息

        Returns:
            dict: 包含订单统计数据的字典
        """
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
        today_stats = today_stats_result[0] if today_stats_result else {}

        trend_sql = '''
                    SELECT
                        DATE (created_at) as date, COUNT (*) as count, SUM (total_amount) as total_amount
                    FROM orders
                    WHERE created_at >= DATE ('now', '-7 days')
                    GROUP BY DATE (created_at)
                    ORDER BY date
                    '''
        trend_data = self.db.execute_query(trend_sql) or []

        return {
            'total': total,
            'by_status': by_status,
            'by_payment': by_payment,
            'today_stats': today_stats,
            'trend_data': trend_data
        }

    def check_room_availability(
            self,
            room_number: str,
            check_in: str,
            check_out: str,
            exclude_order_id: str = None
    ) -> dict:
        """
        检查房间在指定时间段内是否可用

        Args:
            room_number: 房间号
            check_in: 入住日期
            check_out: 退房日期
            exclude_order_id: 排除的订单ID（可选）

        Returns:
            dict: 包含检查结果的字典
        """
        room_sql = "SELECT status FROM rooms WHERE room_number = ?"
        room_result = self.db.execute_query(room_sql, (room_number,))

        if not room_result:
            return {
                'success': False,
                'message': '房间不存在',
                'available': False
            }

        room_status = room_result[0]['status']
        if room_status != '空闲':
            return {
                'success': True,
                'message': f'房间当前状态为{room_status}',
                'available': False
            }

        params = [room_number, check_in, check_out, check_in, check_out]
        exclude_clause = ""
        if exclude_order_id:
            exclude_clause = "AND order_id != ?"
            params.append(exclude_order_id)

        sql = f'''
            SELECT COUNT(*) as count, 
                   GROUP_CONCAT(order_id) as conflict_orders
            FROM orders 
            WHERE room_number = ? 
              AND order_status NOT IN ('已取消', '已完成')
              AND (
                (check_in_date < ? AND check_out_date > ?) OR
                (check_in_date >= ? AND check_in_date < ?) OR
                (check_out_date > ? AND check_out_date <= ?)
              )
              {exclude_clause}
        '''

        result = self.db.execute_query(sql, tuple(params))
        count = result[0]['count'] if result else 0
        conflict_orders = result[0]['conflict_orders'] if result and result[0]['conflict_orders'] else ""

        available = count == 0

        return {
            'success': True,
            'available': available,
            'message': '房间可用' if available else f'房间已被{count}个订单占用',
            'conflict_orders': conflict_orders if not available else ""
        }

    def calculate_payment(self, order_id: str, payment_amount: float) -> dict:
        """
        处理订单支付

        Args:
            order_id: 订单ID
            payment_amount: 支付金额

        Returns:
            dict: 包含支付结果的字典
        """
        order = self._get_order_by_id(order_id)
        if not order:
            return {
                'success': False,
                'message': '订单不存在'
            }

        current_paid = order.get('paid_amount', 0)
        total_amount = order.get('total_amount', 0)
        new_paid = current_paid + payment_amount

        if new_paid <= 0:
            new_status = '未支付'
        elif new_paid >= total_amount:
            new_status = '已支付'
        else:
            new_status = '部分支付'

        update_data = {
            'paid_amount': new_paid,
            'payment_status': new_status
        }

        if self._db_update_order(order_id, update_data):
            return {
                'success': True,
                'message': f'支付成功，当前已付{new_paid}元，支付状态：{new_status}',
                'data': {
                    'order_id': order_id,
                    'total_amount': total_amount,
                    'paid_amount': new_paid,
                    'payment_status': new_status
                }
            }
        else:
            return {
                'success': False,
                'message': '支付更新失败'
            }

    def _insert_order(self, order_data: dict) -> bool:
        sql = '''
              INSERT INTO orders (order_id, customer_id, room_number, employee_id, \
                                  check_in_date, check_out_date, days, total_amount, \
                                  paid_amount, payment_status, order_status, special_requests)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
              '''
        result = self.db.execute_update(sql, (
            order_data.get('order_id'),
            order_data.get('customer_id'),
            order_data.get('room_number'),
            order_data.get('employee_id'),
            order_data.get('check_in_date'),
            order_data.get('check_out_date'),
            order_data.get('days'),
            order_data.get('total_amount', 0.00),
            order_data.get('paid_amount', 0.00),
            order_data.get('payment_status', '未支付'),
            order_data.get('order_status', '预定中'),
            order_data.get('special_requests')
        ))
        return result is not None and result > 0

    def _get_order_by_id(self, order_id: str) -> dict:
        sql = '''
              SELECT o.*,
                     c.name          as customer_name,
                     c.phone         as customer_phone,
                     c.id_card       as customer_id_card,
                     r.room_type,
                     r.price         as room_price,
                     r.status        as room_status,
                     e.employee_name as employee_name
              FROM orders o
                       LEFT JOIN customers c ON o.customer_id = c.id
                       LEFT JOIN rooms r ON o.room_number = r.room_number
                       LEFT JOIN employees e ON o.employee_id = e.employee_id
              WHERE o.order_id = ? \
              '''
        result = self.db.execute_query(sql, (order_id,))
        return result[0] if result else None

    def _db_update_order(self, order_id: str, update_data: dict) -> bool:
        set_fields = []
        params = []
        for field, value in update_data.items():
            if value is not None:
                set_fields.append(f"{field} = ?")
                params.append(value)

        if not set_fields:
            return False

        params.append(order_id)
        sql = f"UPDATE orders SET {', '.join(set_fields)} WHERE order_id = ?"
        result = self.db.execute_update(sql, tuple(params))
        return result is not None and result > 0

    def _db_delete_order(self, order_id: str) -> bool:
        sql = "DELETE FROM orders WHERE order_id = ?"
        result = self.db.execute_update(sql, (order_id,))
        return result is not None and result > 0
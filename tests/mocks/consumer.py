from unittest.mock import Mock


# While amount of test data and mocks is small, we can keep it here
# If it continue to grow, will be moved in separate folder
valid_data = [
 {
  'request_timestamp': '2021-01-01 00:00:00',
  'url': 'https://www.monedo.com/',
  'ip_address': '104.18.91.87',
  'resp_time': '0:00:00.123456',
  'resp_status_code': 200,
  'pattern_found': True,
  'service_name': 'Web metric collection service',
  'comment': 'test'
 },
 {
  'request_timestamp': '2021-01-01 00:00:00',
  'url': 'https://www.monedo.com/',
  'ip_address': '104.18.91.87',
  'resp_time': '0:00:00.123456',
  'resp_status_code': 200,
  'pattern_found': True,
  'service_name': 'Web metric collection service',
  'comment': 'test'
 },
 {
  'request_timestamp': '2021-01-01 00:00:00',
  'url': 'https://www.monedo.com/',
  'ip_address': None,
  'resp_time': None,
  'resp_status_code': 200,
  'pattern_found': None,
  'service_name': 'Web metric collection service',
  'comment': 'test'
 }
]

consumer = Mock()
consumer.fetch_latest.return_value = valid_data

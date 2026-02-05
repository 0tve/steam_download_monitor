import datetime
import os
import re
import time
import winreg

DEFAULT_SPEED = '0 Mbps'
PAUSE_STATUS = 'Пауза'
DOWNLOAD_STATUS = 'Загрузка'


def get_steam_path_from_registry():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
        return os.path.normpath(winreg.QueryValueEx(key, 'SteamPath')[0])


def get_game_name(steam_path, appid):
    manifest_path = os.path.join(
        steam_path, 'steamapps', f'appmanifest_{appid}.acf')
    with open(manifest_path, 'r', encoding='utf-8') as f:
        match = re.search(r'"name"\s+"([^"]+)"', f.read())
        if match:
            return match.group(1)


def read_last_log_files(log_path, num_lines=100):
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-num_lines:] if len(lines) >= num_lines else lines
    except (FileNotFoundError, PermissionError) as e:
        print(f'Ошибка чтения лога: {e}')
        return []


def get_appid(lines):
    appid_pattern = re.compile(r'AppID\s+(\d+)')
    for line in reversed(lines):
        match = appid_pattern.search(line)
        if match:
            return match.group(1)


def get_download_status(lines, threshold_minutes=2):
    speed_pattern = re.compile(
        r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Current download rate:\s+([\d.]+ Mbps)')
    now = datetime.datetime.now()
    speed = DEFAULT_SPEED
    status = PAUSE_STATUS

    for line in reversed(lines):
        match = speed_pattern.search(line)
        if match:
            timestamp_str, speed_val = match.groups()
            try:
                log_time = datetime.datetime.strptime(
                    timestamp_str, '%Y-%m-%d %H:%M:%S')
                if now - log_time < datetime.timedelta(minutes=threshold_minutes):
                    status = DOWNLOAD_STATUS
                speed = speed_val
                break
            except ValueError:
                continue
    return speed, status


def analyze_log(log_file):
    lines = read_last_log_files(log_file)
    if not lines:
        return None, DEFAULT_SPEED, PAUSE_STATUS
    appid = get_appid(lines)
    speed, status = get_download_status(lines)
    return appid, speed, status


def run_monitoring(steam_path):
    for i in range(5):
        start = datetime.datetime.now()

        appid, speed, status = analyze_log(
            os.path.join(steam_path, 'logs', 'content_log.txt'))
        game_name = get_game_name(steam_path, appid) if appid else ''
        timestamp = start.strftime("[%H:%M:%S]")
        print(f'{timestamp} Игра: {game_name} | Скорость: {speed} | Статус: {status}')

        if i == 4:
            print('--- Мониторинг завершен ---\n')
            break

        end = datetime.datetime.now()
        time_elapsed = end - start
        time_left_seconds = 60 - time_elapsed.total_seconds()

        if time_left_seconds > 0:
            time.sleep(time_left_seconds)
        else:
            pass


def main():
    steam_path = get_steam_path_from_registry()
    print("Команды: 'go' - запустить мониторинг на 5 минут, любой другой текст - выход")
    while True:
        user_input = input('User> ').strip().lower()
        if user_input == 'go':
            run_monitoring(steam_path)
        else:
            break


if __name__ == '__main__':
    main()

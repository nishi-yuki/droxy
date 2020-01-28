#! /usr/bin/env python3
# vim :setfiletype python3

''' Droxy Prototype

Proxy設定をssidごとに行うツールdroxyのプロトタイプ版です。プロトタイプ版なので
日本語が多いです。コメントもゆるふわです。ゆるしてね。
'''

import sys
import os
import configparser
from pathlib import Path
from subprocess import run, PIPE, DEVNULL
from typing import Callable, Sequence, Dict, Optional


xdg_config_home = os.getenv('XDG_CONFIG_HOME', '.config')
SSID_PROXY_CONFIG_FILE_NAME = 'ssid-proxy.conf'
SSID_PROXY_CONFIG_FILE_PATHS = [
    Path(__file__).parent/SSID_PROXY_CONFIG_FILE_NAME,
    # 下のパスは nishi-yuki/proxy-conf-by-ssid との互換性のため
    Path.home()/xdg_config_home/SSID_PROXY_CONFIG_FILE_NAME,
    Path.home()/xdg_config_home/'droxy'/SSID_PROXY_CONFIG_FILE_NAME,
]
HTTP_PROXY_KEY = 'http_proxy'
HTTPS_PROXY_KEY = 'https_proxy'

name2cmd: Dict[str, Callable] = {}
proxy_config: configparser.ConfigParser


def main():
    argc = len(sys.argv)
    status = 1

    try:
        init_config()
    except ConfigFileNotFoundError:
        print('エラー:', 'ssid-proxy.confファイルが見つかりません\n'
              'ssid-proxy.confファイルは以下の場所のいずれかに配置される必要があります\n'
              + '  ' + '\n  '.join([str(p.absolute())
                                    for p in SSID_PROXY_CONFIG_FILE_PATHS]),
              file=sys.stderr)
        exit(105)

    if argc == 1:
        droxy_cmd_handler()
    else:
        status = call_cmd(sys.argv[1:])
    exit(status)


def droxy_cmd_handler():
    """　"$ droxy" で呼び出された関数の中身

    droxy_cmd_handlerはdroxyコマンドを呼び出されたときに実行される関数です。\
    droxyコマンドはdroxy自体の操作を行います。
    """
    print('Droxy 0.0.1')


def call_cmd(cmd_line: Sequence[str]) -> int:
    """ シェルコマンドの呼び出し

    call_cmd は cmd_name で指定されたシェルコマンドにプロクシ設定を施した上で\
    実行する関数です。

    Args:
        cmd_name (str): 呼び出すシェルコマンド

    Returns:
        int: ステータスコード
    """
    cmd = cmd_line[0]
    args = cmd_line[1:]
    proxys = get_proxys(get_ssid())
    if cmd in name2cmd:
        status = name2cmd[cmd](args, proxys)
    else:
        status = default(cmd, args, proxys)
    return status


class ConfigFileNotFoundError(Exception):
    pass


def init_config():
    "設定ファイルを読み込みます"
    global proxy_config
    proxy_config = configparser.ConfigParser()
    config_path = None

    # 優先度の高い順に設定ファイルを探す
    for path in SSID_PROXY_CONFIG_FILE_PATHS:
        if path.exists():
            config_path = path
            break
    # 設定ファイルが見つからなかったとき
    if not config_path:
        raise ConfigFileNotFoundError
    proxy_config.read(config_path)


def get_ssid() -> Optional[str]:
    """ 現在のSSID名を取得します

    Returns:
        str: SSID
    """
    compproc = run(['iwgetid', '--raw'], stdout=PIPE)
    status = compproc.returncode
    try:
        ssid = compproc.stdout.decode('UTF8').strip()
    except UnicodeDecodeError:
        return ''

    if status == 0:
        return ssid
    else:
        return None


def get_proxys(ssid: Optional[str]) -> dict:
    """ SSID名からプロクシ設定を取得します

    Args:
        ssid (Optional[str]): ssid名 Noneを渡した場合、空の辞書が返されます。
    """
    if ssid in proxy_config:
        return dict(proxy_config[ssid])  # type: ignore
    else:
        return {}


def command(name: str) -> Callable:
    """ シェルコマンドラッパー関数を登録するデコレータ

    Args:
        name (str): コマンド名 pythonの関数名で使用可能な文字集合とコマンド名として\
        使用可能な文字集合は異なるため、このような引数を必要とします。
    Returns:
        int: ステータスコード
    """
    def decorator(f: Callable[[Sequence[str], dict], int]):
        name2cmd[name] = f
    return decorator


################################################################################
#    Droxy内部コマンド
################################################################################


@command('dummy-cmd')  # コマンド名に"-" つかえます
def dummy_command(args: Sequence[str], proxys: dict) -> int:
    '''テスト用のダミーコマンド
    Droxyの動作チェックができます
    '''
    print('dummy-cmd called!')
    print('Execed like this:', ('dummy-cmd',) + tuple(args))
    print('proxys =', proxys)
    print('bye!')
    return 0


@command('dummy-status-code')
def dummy_status_code(args: Sequence[str], proxys: dict) -> int:
    code = 166
    try:
        code = int(args[0])
    except:
        print('引数エラー')
    return code


@command('sudo')    # 名前については要検討
def sudo(args: Sequence[str], proxys: dict) -> int:
    """ 管理者権限で実行する
    droxyを管理者権限で実行するための特殊な内部コマンド
    """
    run(['sudo', Path(__file__).absolute()] + args)

################################################################################
#    外部コマンド
################################################################################


@command('git')
def git(args: Sequence[str], proxys: dict) -> int:
    try:
        set_git_http_proxy(proxys)
        run(['git'] + args)
    finally:
        unset_git_http_proxy()


################################################################################
#    その他すべて
################################################################################


def default(cmd: str, args: Sequence[str], proxys: dict) -> int:
    upper_proxys = {k.upper(): v for k, v in proxys.items()}
    environ = os.environ
    environ.update(proxys)
    environ.update(upper_proxys)
    result = run((cmd,) + tuple(args), env=environ)
    return result.returncode


################################################################################
#   Utils
################################################################################

# git utils

def set_git_http_proxy(proxys: dict):
    if HTTPS_PROXY_KEY in proxys:
        run(['git', 'config', '--global', 'https.proxy', proxys[HTTPS_PROXY_KEY]])
    if HTTP_PROXY_KEY in proxys:
        run(['git', 'config', '--global', 'http.proxy', proxys[HTTPS_PROXY_KEY]])


def unset_git_http_proxy():
    run(['git', 'config', '--global', '--unset', 'https.proxy'])
    run(['git', 'config', '--global', '--unset', 'http.proxy'])
    # unset section if empty
    if is_gitconfig_section_empty('https'):
        run(['git', 'config', '--global', '--remove-section', 'https'])
    if is_gitconfig_section_empty('http'):
        run(['git', 'config', '--global', '--remove-section', 'http'])


def is_gitconfig_section_empty(section_name: str) -> bool:
    rc = run(['git', 'config', '--global', '--get-regexp', '^'+section_name+'\\.'],
             stdout=DEVNULL).returncode
    return rc != 0


if __name__ == "__main__":
    main()

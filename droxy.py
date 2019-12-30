#! /usr/bin/env python3
# vim :setfiletype python3

''' Droxy Prototype

Proxy設定をssidごとに行うツールdroxyのプロトタイプ版です。プロトタイプ版なので
日本語が多いです。コメントもゆるふわです。ゆるしてね。
'''

import argparse
import sys
import os
from subprocess import run
from typing import Callable, Sequence, Dict


name2cmd: Dict[str, Callable] = {}


def main():
    argc = len(sys.argv)

    status = 1
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
    proxys = {'http': 'proxy.example.com'}
    if cmd in name2cmd:
        status = name2cmd[cmd](args, proxys)
    else:
        status = default(cmd, args, proxys)
    return status


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


def default(cmd: str, args: Sequence[str], proxys: dict) -> int:
    environ = os.environ
    environ.update(proxys)
    result = run((cmd,) + tuple(args), env=environ)
    return result.returncode


if __name__ == "__main__":
    main()

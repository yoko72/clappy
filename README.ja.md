# clappy

コマンドライン引数の処理がシンプルに書けるライブラリです。

clappyあり:

    import clappy as cl

    foo = cl.parse("--foo")
    bar = cl.parse("--bar", is_flag=True)

clappyなし:

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--foo")
    parser.add_argument("--bar", action="store_true")
    args = parser.parse_args()
    foo = args.foo
    bar = args.bar


サブコマンドを使う場合は特に、読みやすくなります。

clappyあり:

    import clappy as cl

    if cl.subcommand("foo").invoked:
        opt = cl.parse("--foo_opt")
    elif cl.subcommand("bar").invoked:
        opt = cl.parse("--bar_opt")

clappyなし:

    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparser1 = subparsers.add_parser("foo")
    subparser1.add_argument("--foo_opt")
    subparser2 = subparsers.add_parser("bar")
    subparser2.add_argument("--bar_opt")
    args = parser.parse_args()

    if hasattr(args, "foo_opt"):
        opt = args.foo_opt
    elif hasattr(args, "bar_opt"):
        opt = args.bar_opt


また、複数のモジュールがコマンドライン引数を受け取る場合にも特に効果的です。
通常、同一のパーサーやパース結果を複数モジュール間で受け渡しながらこねくり回す必要があります。
しかし、clappyであれば各モジュールで個々にparseの処理を書くことができます。


## インストール

`pip install clappy`

## 使い方

argparseのwrapperのため、主要関数に同じ引数を使うことができます。

clappy.parse(*args, **kwargs)に渡す*args, **kwargsはそれぞれargparse.ArgumentParser().add_argument(*args, **kwargs)と同一です。
[受け取れる引数一覧と説明はこちら。](https://docs.python.org/ja/3/library/argparse.html#the-add-argument-method)

ただし、clappy.parseでは独自にis_flagというキーワード専用引数を受け取ることができます。
これはargparseのadd_argumentで言う、action="store_true"を渡すのと全く同じです。
"store_true"という文字列を毎度正確に思い出せなくてもいいようにするためのものです。

"is_flag"がTrueとされているオプションは、コマンドライン上で値を受け取りません。
ただオプションが指定されたかどうかというboolを返すのみのflagになります。

### Subcommand
clappy.subcommand()でサブコマンドの処理が書けます。

このsubcommand関数は、subparsers.add_parser()と同じ引数を受け取れます。
[受け取れる引数一覧と説明はこちら。](https://docs.python.org/ja/3/library/argparse.html#argumentparser-objects)

但し、位置引数として受け取れるのは最初の1つのみとなっている点に注意です。


    subcommand = clappy.subcommand(name, **kwargs)  # 1

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="foo")
    subparser = subparsers.add_parser(name, **kwargs)  # 2
    
    # 1と２には全く同じ引数が利用できます。

また、各サブコマンドが呼び出されたかどうかを、明示的にも暗示的にも書くことができます。
下記2つの例は同価です。

    sc = clappy.subcommand("foo")
    if sc.invoked:
        # do smth

    if clappy.subcommand("foo"):
        # do smth

### ヘルプ文の自動生成

-hもしくは--helpのオプションと共にスクリプトが実行された際に使い方を出力したいケースがあると思います。
そのヘルプをclappyで自動生成する方法は2つあります。

1. clappy.create_help()を全てのパースが終わった後に実行


    clappy.parse("--foo")
    clappy.parse("--bar")
    clappy.create_help()

ヘルプオプション付きで実行されたプログラムは、受け取ることができる引数の一覧を取得した後、各引数の説明を出力するのが一般的です。
その後に続くコードを実行するのは無駄なので、引数一覧取得後にはプログラムを終了することになります。

つまり、引数一覧の取得がどのタイミングで終わったのかを知る必要があります。

そこで、clappyでは全てのparseが終了したタイミングにclappy.create_help()を明記することで、
ヘルプが自動生成できるようになります。

2. with文でパーサーを受け取る


    with clappy.get_parser():
        clappy.parse("--foo")
        clappy.parse("bar")

With文があるとparseの終了タイミングがわかるのでヘルプを自動生成することができます。

また、上記2つどちらのやり方でもparseされなかった引数が残っていた場合にログに警告が出力されるようになります。


### Parserを引数付きで生成したい

with文と共に、parserに引数を渡してのインスタンス化を推奨します。

    with clappy.get_parser(*args, **kwargs):
        clappy.parse("--foo")
        clappy.parse("bar")

この関数get_parserはargparse.ArgumentParser(*args, **kwargs)と同じ引数を受け取れます。
[受け取れる引数一覧と説明はこちら。](https://docs.python.org/ja/3/library/argparse.html#argumentparser-objects)
上記のようにwith文と実行することで、 ヘルプの作成、parseされなかったコマンドライン引数があった場合の警告があるためです。

但し、with文のブロック内で全てのparseを実行しなければいけなくなることに注意してください。

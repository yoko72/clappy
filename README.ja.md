# clappy

コマンドライン引数の受け取り処理がシンプルに書けるライブラリです。

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
    try:
        opt = args.foo_opt
    except AttributeError:
        try:
            opt = args.bar_opt
        except AttributeError:
            pass


また、複数のモジュールがコマンドライン引数を受け取る場合には特に強力です。
通常、同一のパーサーやパース結果を複数モジュール間で受け渡しながらこねくり回す必要があります。
しかし、clappyであれば各モジュールで個々にparseの処理を書くことができます。


## インストール

`pip install clappy`

## 使い方

argparseのwrapperのため、同じ引数を使うことができます。

clappy.parse(*args, **kwargs)に渡す*args, **kwargsはそれぞれargparse.ArgumentParser().add_argument(*args, **kwargs)と同一です。
ただし、clappy.parseでは独自にis_flagというキーワード専用引数を受け取ることができます。
これはargparseのadd_argumentで言う、action="store_true"を渡すのと同じです。
"store_true"という文字列を毎度正確に思い出せなくてもいいようにするためのものです。
"store_True", "store true"などにより間違い、無駄に調べる時間を抑止します。

"is_flag"がTrueとされているオプションは、コマンドライン上で値を受け取りません。
ただオプションが指定されたかどうかというboolを返すのみのflagになります。

### Subcommand
clappy.subcommand()でサブコマンドの処理が書けます。

このsubcommand関数は、subparsers.add_parser()と同じ引数を受け取れます。

    subcommand = clappy.subcommand(*args, **kwargs)  # 1

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="foo")
    subparser = subparsers.add_parser(*args, **kwargs)  # 2
    
    # 1と２には全く同じ引数が利用できます。

また、各サブコマンドが呼び出されたかどうかを、明示的にも暗示的にも書くことができます。
下記2つの例は同価です。

    sc = clappy.subcommand("foo")
    if sc.invoked:
        # do smth

    if clappy.subcommand("foo"):
        # do smth

### ヘルプ文の自動生成

もしヘルプの自動生成がほしければ、clappy.create_help()をコードに足してください。
この関数は、全てのparseが終わった後に足される必要があります。

### Parserを生成したい

通常、clappyではParserが自動で生成されますが、自分で生成することもできます。
clappy.initialize_parser(*args, **kwargs)を使ってください。
この関数はargparse.ArgumentParser(*args, **kwargs)と同じ引数を受け取れます。

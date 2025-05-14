# avatar_ros

![avatar](./doc/avatar.gif)

```console
$ colcon build
$ source install/setup.bash
$ ros2 run avatar_ros avatar_node
```

# TODO

## 完了
- [x] m5stack-avatarからの移植を行う
- [x] 描画系をpygameに変更

## 対応予定
- [ ] 全画面表示への対応（F11で切り替え）
- [ ] バツボタンでプログラムが終了するように変更
- [ ] GazeをPublishする処理の追加

## 参考
参照するm5stack-avatarのコードは以下のURLです。
https://github.com/stack-chan/m5stack-avatar/tree/master

移植する機能は以下の通りです。
- 顔の表示機能
- リップシンク
- 表情変化
- 文字表示バルーン
- 音声合成
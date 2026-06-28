# 天下无贼

一个用 Python 开发的 macOS 菜单栏报警工具。

## 界面预览

![天下无贼菜单栏界面](assets/menu-screenshot.png)

## 免责声明

本应用基于兴趣开发，免费提供使用。使用本应用过程中如出现电脑、数据、财物或其他任何损失，开发者不承担任何责任。

本应用的目的只是临时震慑别有用心的人，无法避免被偷，也不能替代个人看管和安全环境。它更像是“防君子不防小人”的提醒工具。电脑仍应尽量放在安全环境中使用和保存，例如我个人一般会选择先锋书店五台山总店这类相对安全的地方临时使用。

社恐者慎用，监控开启情况下，误触会很社死。解决方法：抱着电脑就跑，要是脸皮厚可以优雅地关闭监控。

## 功能

- 电脑监控：拔掉电源或合盖都会触发报警。
- 充电器触发：插回电源后停止播报并继续监控。
- 合盖触发：合盖后锁存报警，开盖后也继续报警，直到验证关闭密码。
- 公共配置：报警音量、报警词汇、报警声音、关闭密码。
- 中英文界面切换，默认中文。
- 任何关闭监控动作都需要关闭密码。
- 报警监控运行期间不允许修改公共配置。
- 开启监控后，“开启电脑监控”会灰化，避免重复开启。
- 关闭监控时，如果系统休眠设置尚未恢复，菜单会显示“监控状态：系统设置待恢复”，并禁止重新开启，直到恢复成功。

## 当前默认配置

配置文件位置：

```text
~/.tianxiawuzei/config.json
```

默认值：

```json
{
  "alarm_volume": 60,
  "alarm_text": "请不要碰我电脑",
  "close_password": "1111",
  "voice": "Sin-ji",
  "speech_rate": 165,
  "language": "zh"
}
```

## 安装依赖

```bash
cd tianxiawuzei
python3 -m pip install -r requirements.txt
```

## 运行

```bash
cd tianxiawuzei
PYTHONPATH=. python3 -m tianxiawuzei
```

启动后，菜单栏会出现“天下无贼”。

## 电脑监控权限说明

电脑监控包含合盖触发报警，需要临时执行：

```bash
sudo pmset -a disablesleep 1
```

关闭时会恢复：

```bash
sudo pmset -a disablesleep 0
```

因此电脑监控开启或关闭时，macOS 可能要求输入管理员密码。

关闭逻辑分两段：

- 关闭密码正确后，电脑监控即视为关闭成功。
- 只有本次确实执行了系统休眠恢复动作，App 才会提示恢复成功或恢复失败。

如果关闭监控时取消或关闭了系统密码窗口，报警会停止，但 `SleepDisabled` 可能仍未恢复为 0。此时 App 会提示：

```text
未能成功恢复系统休眠
```

菜单栏状态会显示：

```text
监控状态：系统设置待恢复
```

此时“开启电脑监控”会保持灰化，避免在系统设置未恢复时重复开启。App 会自动重试恢复，也可以在菜单栏点击“恢复系统休眠设置”。恢复成功后，菜单栏会回到“监控状态：未开启”，并重新允许开启电脑监控。

如果仍然失败，可以手动执行：

```bash
sudo pmset -a disablesleep 0
```

如果开启电脑监控前 `SleepDisabled` 本来就是 1，App 不会主动修改系统休眠设置；关闭监控时也不会执行恢复动作，因此不会提示系统休眠恢复成功或失败。

## 运行测试

```bash
cd tianxiawuzei
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## 打包

```bash
cd tianxiawuzei
python3 -m pip install -r requirements.txt
python3 setup.py py2app
```

打包产物位于：

```text
dist/天下无贼.app
```

## 后续可做

- 加语音选择菜单。
- 增加开机自启动选项。

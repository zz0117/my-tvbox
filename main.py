from sources.zbds import get_live_channels as get_zbds_channels
from sources.wangzi import get_live_channels as get_wangzi_channels

from pathlib import Path

# 仓库根目录
BASE_DIR = Path(__file__).resolve().parent

# 固定输出位置
LIVE_FILE = BASE_DIR / "live" / "live.txt"


# =====================
# 合并频道
# 同名频道合并线路
# =====================

def merge_channels(items):
    print(
        "合并频道"
    )

    channels = {}

    order = []

    for item in items:

        key = (
            item["group"],
            item["name"]
        )

        if key not in channels:
            channels[key] = []

            order.append(key)

        channels[key].append(
            item["url"]
        )

    result = []

    index = 0

    for key in order:

        group, name = key

        urls = []

        seen = set()

        for url in channels[key]:

            if url in seen:
                continue

            seen.add(url)

            urls.append(url)

        result.append(

            {

                "index": index,

                "group": group,

                "name": name,

                # 多线路
                "url": "#".join(urls)

            }

        )

        index += 1

    print(
        "合并后频道:",
        len(result)
    )

    return result


# =====================
# 保存live.txt
# =====================

def save_live(channels):
    LIVE_FILE.parent.mkdir(

        parents=True,

        exist_ok=True

    )

    with open(

            LIVE_FILE,

            "w",

            encoding="utf-8"

    ) as f:

        current_group = None

        for item in channels:

            group = item["group"]

            if group != current_group:
                current_group = group

                f.write(

                    f"{group},#genre#\n"

                )

            f.write(

                f'{item["name"]},{item["url"]}\n'

            )


# =====================
# 主程序
# =====================

def main():
    print(
        "开始更新直播源"
    )

    # =====================
    # 王子源
    # 优先级最高
    # =====================

    print(
        "更新王子源"
    )

    wangzi_channels = get_wangzi_channels()

    # =====================
    # zbds
    # =====================

    print(
        "更新zbds"
    )

    zbds_channels = get_zbds_channels()

    # =====================
    # 合并
    #
    # 王子在前
    # zbds补充
    #
    # =====================

    all_channels = (

            wangzi_channels

            +

            zbds_channels

    )

    print(

        "原始频道:",

        len(all_channels)

    )

    channels = merge_channels(

        all_channels

    )

    print(

        "最终频道:",

        len(channels)

    )

    print(

        "写入:",

        LIVE_FILE

    )

    save_live(

        channels

    )

    print(
        "更新完成"
    )


if __name__ == "__main__":
    main()

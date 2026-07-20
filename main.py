from sources.zbds import get_live_channels
from pathlib import Path


# 仓库根目录
BASE_DIR = Path(__file__).resolve().parent


# 固定输出位置
LIVE_FILE = BASE_DIR / "live" / "live.txt"



def save_live(channels):

    # 确保目录存在
    LIVE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # 覆盖写入
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



def main():


    print(
        "开始更新直播源"
    )


    channels = get_live_channels()



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
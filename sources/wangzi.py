import requests

SOURCE = (
    "http://wangziduoqing.com/yuan/zb.txt"
)


def get_headers():
    return {

        "User-Agent":
            "Mozilla/5.0",

        "Accept":
            "*/*"

    }


# =====================
# 下载
# =====================

def download_source():
    print(
        "下载王子源"
    )

    r = requests.get(

        SOURCE,

        timeout=15,

        headers=get_headers()

    )

    content = r.content

    for enc in (
            "utf-8",
            "gb18030",
            "gbk"
    ):

        try:

            return content.decode(enc)

        except UnicodeDecodeError:

            continue

    return content.decode(
        "utf-8",
        errors="ignore"
    )


# =====================
# 解析
# =====================

def parse_txt(text):
    print(
        "解析王子源"
    )

    result = []

    group = "其他"

    seen = set()

    index = 0

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if "#genre#" in line:
            group = line.replace(

                ",#genre#",

                ""

            ).strip()

            continue

        if "," not in line:
            continue

        name, url = line.split(

            ",",

            1

        )

        name = name.strip()

        url = url.strip()

        if not url.startswith(
                "http"
        ):
            continue

        # 核心：
        # 只保留m3u8

        if ".m3u8" not in url.lower():
            continue

        if url in seen:
            continue

        seen.add(url)

        result.append(

            {

                "index": index,

                "group": group,

                "name": name,

                "url": url

            }

        )

        index += 1

    print(

        "王子m3u8:",

        len(result)

    )

    return result


# =====================
# 外部调用
# =====================

def get_live_channels():
    text = download_source()

    return parse_txt(text)

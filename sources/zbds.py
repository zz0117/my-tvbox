import requests
import time
import concurrent.futures

from urllib.parse import urlparse

SOURCE = (
    "https://live.zbds.top/tv/iptv4.txt"
)

TIMEOUT = 5

MAX_WORKERS = 50


# =====================
# 请求头
# =====================

def get_headers(url):
    parsed = urlparse(url)

    return {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Referer":
            f"{parsed.scheme}://{parsed.netloc}/",
        "Connection":
            "keep-alive"
    }


# =====================
# 下载源
# =====================

def download_source():
    print("下载源")

    r = requests.get(
        SOURCE,
        timeout=15,
        headers=get_headers(SOURCE)
    )

    r.encoding = "utf-8"

    return r.text


# =====================
# 解析
# =====================

def parse_txt(text):
    print("解析")

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
            )

            continue

        if "," not in line:
            continue

        name, url = line.split(
            ",",
            1
        )

        url = url.strip()

        if not url.startswith(
                "http"
        ):
            continue

        if url in seen:
            continue

        seen.add(url)

        result.append(
            {
                "index": index,
                "group": group,
                "name": name.strip(),
                "url": url
            }
        )

        index += 1

    print(
        "去重后:",
        len(result)
    )

    return result


# =====================
# 获取第一片
# =====================

def get_first_segment(m3u8, url):
    base = url.rsplit(
        "/",
        1
    )[0]

    for line in m3u8.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith(
                "http"
        ):
            return line

        return (
                base
                +
                "/"
                +
                line
        )

    return None


# =====================
# 检测
# =====================

def check_stream(item):
    try:

        start = time.time()

        r = requests.get(
            item["url"],
            timeout=TIMEOUT,
            headers=get_headers(item["url"])
        )

        if r.status_code != 200:
            return None

        m3u8 = r.text

        if "#EXTM3U" not in m3u8:
            return None

        segment = get_first_segment(
            m3u8,
            item["url"]
        )

        if not segment:
            return None

        ts = requests.get(
            segment,
            timeout=TIMEOUT,
            headers=get_headers(segment),
            stream=True
        )

        if ts.status_code != 200:
            return None

        size = 0

        for chunk in ts.iter_content(
                1024
        ):

            size += len(chunk)

            if size >= 10240:
                break

        if size < 1024:
            return None

        item["speed"] = (
                time.time() - start
        )

        return item



    except Exception:

        return None


# =====================
# 批量检测
# =====================

def check_all(items):
    print(
        "开始检测:",
        len(items)
    )

    result = []

    total = len(items)

    finish = 0

    with concurrent.futures.ThreadPoolExecutor(

            max_workers=MAX_WORKERS

    ) as pool:

        futures = [

            pool.submit(
                check_stream,
                item
            )

            for item in items

        ]

        for future in concurrent.futures.as_completed(
                futures
        ):

            finish += 1

            data = future.result()

            if data:

                result.append(data)

                print(
                    f"[{finish}/{total}]有效:",
                    data["name"],
                    round(
                        data["speed"],
                        2
                    )
                )


            elif finish % 50 == 0:

                print(
                    f"[{finish}/{total}]检测中"
                )

    print(
        "有效:",
        len(result)
    )

    # ★关键：恢复源顺序

    result.sort(
        key=lambda x: x["index"]
    )

    return result


# =====================
# 合并多线路
# =====================

def merge_channels(items):
    print(
        "整理频道"
    )

    channels = {}

    for item in items:

        key = (

            item["group"],

            item["name"]

        )

        if key not in channels:
            channels[key] = []

        channels[key].append(item)

    result = []

    for key, values in channels.items():

        group, name = key

        # 这里只排序线路速度
        # 不影响频道顺序

        values.sort(
            key=lambda x: x["speed"]
        )

        urls = []

        for item in values[:5]:
            urls.append(
                item["url"]
            )

        result.append(
            {
                "index":
                    values[0]["index"],

                "group": group,

                "name": name,

                "url": "#".join(urls)
            }
        )

    # ★关键：恢复频道顺序

    result.sort(
        key=lambda x: x["index"]
    )

    return result


# =====================
# 总入口
# =====================

def get_live_channels():
    text = download_source()

    items = parse_txt(text)

    valid = check_all(items)

    result = merge_channels(valid)

    print(
        "最终输出:",
        len(result)
    )

    return result

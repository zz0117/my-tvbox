import requests
import time
import concurrent.futures

from urllib.parse import urlparse


SOURCE = (
    "https://live.zbds.top/tv/iptv4.txt"
)


TIMEOUT = (3, 5)


MAX_WORKERS = 50



# =====================
# 请求头
# =====================

def get_headers(url):

    parsed = urlparse(url)

    return {

        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36",

        "Accept":
            "*/*",

        "Referer":
            f"{parsed.scheme}://{parsed.netloc}/",

        # 扫描不要长连接
        "Connection":
            "close"
    }





# =====================
# 下载
# =====================

def download_source():

    print(
        "下载源"
    )


    r = requests.get(

        SOURCE,

        timeout=15,

        headers=get_headers(SOURCE)

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

            pass



    return content.decode(

        "utf-8",

        errors="ignore"

    )





# =====================
# 解析
# =====================

def parse_txt(text):

    print(
        "解析"
    )


    result=[]


    group="其他"


    seen=set()


    index=0



    for line in text.splitlines():


        line=line.strip()



        if not line:

            continue



        if "#genre#" in line:


            group=line.replace(

                ",#genre#",

                ""

            ).strip()


            continue



        if "," not in line:

            continue



        name,url=line.split(

            ",",

            1

        )


        url=url.strip()



        if not url.startswith(
            "http"
        ):

            continue



        if url in seen:

            continue



        seen.add(url)



        result.append({

            "index":index,

            "group":group,

            "name":name.strip(),

            "url":url

        })


        index+=1



    print(

        "总线路:",

        len(result)

    )


    return result





# =====================
# 获取第一片TS
# =====================

def get_first_segment(text,url):


    base=url.rsplit(

        "/",

        1

    )[0]



    for line in text.splitlines():


        line=line.strip()



        if not line:

            continue



        if line.startswith("#"):

            continue



        if line.startswith("http"):

            return line



        return base+"/"+line



    return None





# =====================
# 单个检测
# =====================

def check_stream(item):

    try:


        start=time.time()



        # m3u8
        with requests.get(

            item["url"],

            timeout=TIMEOUT,

            headers=get_headers(

                item["url"]

            ),

            stream=True

        ) as r:



            if r.status_code != 200:

                return None



            data=b""


            for chunk in r.iter_content(

                4096

            ):

                data += chunk


                if len(data)>=8192:

                    break



        text=data.decode(

            "utf-8",

            errors="ignore"

        )



        if "#EXTM3U" not in text:

            return None



        segment=get_first_segment(

            text,

            item["url"]

        )


        if not segment:

            return None




        # 下载一点TS验证

        with requests.get(

            segment,

            timeout=TIMEOUT,

            headers=get_headers(segment),

            stream=True

        ) as ts:



            if ts.status_code != 200:

                return None



            size=0



            for chunk in ts.iter_content(

                1024

            ):


                size+=len(chunk)


                if size>=10240:

                    break



            if size<1024:

                return None




        item["speed"]=round(

            time.time()-start,

            2

        )


        return item



    except Exception:

        return None





# =====================
# 多进程检测
# =====================

def check_all(items):


    print(

        "开始检测:",

        len(items)

    )



    result=[]


    total=len(items)


    finish=0



    with concurrent.futures.ProcessPoolExecutor(

        max_workers=MAX_WORKERS

    ) as pool:



        futures={

            pool.submit(

                check_stream,

                item

            ):item

            for item in items

        }



        for future in concurrent.futures.as_completed(

            futures

        ):



            finish+=1



            try:

                data=future.result(

                    timeout=15

                )


            except Exception:

                data=None




            if data:


                result.append(data)


                print(

                    f"[{finish}/{total}]有效:",

                    data["name"],

                    data["speed"]

                )


            elif finish % 50 == 0:


                print(

                    f"[{finish}/{total}]检测中"

                )




    print(

        "有效:",

        len(result)

    )



    # 恢复原顺序

    result.sort(

        key=lambda x:x["index"]

    )



    return result





# =====================
# 合并频道
# =====================

def merge_channels(items):


    print(

        "整理频道"

    )



    channels={}


    order=[]



    for item in items:


        key=(

            item["group"],

            item["name"]

        )



        if key not in channels:


            channels[key]=[]

            order.append(key)



        channels[key].append(item)



    result=[]



    for index,key in enumerate(order):


        group,name=key


        values=channels[key]



        values.sort(

            key=lambda x:x["speed"]

        )



        urls=[]


        for item in values[:5]:

            urls.append(

                item["url"]

            )



        result.append({

            "index":index,

            "group":group,

            "name":name,

            "url":"#".join(urls)

        })



    return result





# =====================
# 外部调用
# =====================

def get_live_channels():


    text=download_source()


    items=parse_txt(text)


    valid=check_all(items)


    result=merge_channels(valid)



    print(

        "最终输出:",

        len(result)

    )


    return result
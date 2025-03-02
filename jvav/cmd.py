# -*- coding: UTF-8 -*-
import os
import logging
import argparse
import langdetect
import jvav

PATH_ROOT = os.path.expanduser("~") + "/.jvav"
if not os.path.exists(PATH_ROOT):
    os.makedirs(PATH_ROOT)


class Logger:
    def __init__(self, log_level: int, path_log_file: str):
        """初始化日志记录器

        :param int log_level: 记录级别
        :param str path_log_file: 日志文件位置
        """
        self.logger = logging.getLogger()
        self.logger.addHandler(self.get_file_handler(path_log_file))
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(log_level)

    def get_file_handler(self, file):
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        )
        return file_handler


LOG = Logger(logging.INFO, f"{PATH_ROOT}/log.txt").logger


class JvavArgsParser:
    def __init__(self):
        parser = argparse.ArgumentParser()
        # 搜索番号
        parser.add_argument("-av1", type=str, default="", help="后接番号，通过 JavBus 搜索该番号")
        parser.add_argument("-av2", type=str, default="", help="后接番号，通过 Sukebei 搜索该番号")
        parser.add_argument("-nc", action="store_true", help="过滤出高清有字幕磁链")
        parser.add_argument("-uc", action="store_true", help="过滤出无码磁链")
        # 搜索演员
        parser.add_argument("-sr", type=str, default="", help="后接演员名字, 根据演员名字获取高分番号列表")
        parser.add_argument("-srn", type=str, default="", help="后接演员名字, 根据演员名字获取最新番号列表")
        # 获取预览视频
        parser.add_argument(
            "-pv1", type=str, default="", help="后接番号, 通过 DMM 获取番号对应预览视频"
        )
        parser.add_argument(
            "-pv2", type=str, default="", help="后接番号, 通过 Avgle 获取番号对应预览视频"
        )
        # 获取排行榜
        parser.add_argument("-tp", action="store_true", help="获取 DMM 女优排行榜前 25 位")
        # 配置代理
        parser.add_argument(
            "-p",
            "--proxy",
            type=str,
            default="",
            help="后接代理服务器地址, 默认读取环境变量 http_proxy 的值",
        )
        self.parser = parser
        self.args = None

    def handle_code(self, code: int, res):
        """处理结果

        :param int code: 状态码
        :param any res: 结果
        """
        if code != 200:
            LOG.error(f"{code}: 操作失败")
            return
        LOG.info(res)

    def parse(self):
        """解析命令行参数"""
        parser = self.parser
        self.args = parser.parse_args()

    def exec(self):
        """根据参数表自行相应操作"""
        if not self.args:
            self.parser.print_help()
            return
        args = self.args
        env_proxy = os.getenv("http_proxy")
        if args.proxy == "" and env_proxy:
            args.proxy = env_proxy
        if args.av1 != "":
            self.handle_code(
                *jvav.JavBusUtil(proxy_addr=args.proxy).get_av_by_id(
                    id=args.av1, is_nice=args.nc, is_uncensored=args.uc
                )
            )
        elif args.av2 != "":
            self.handle_code(
                *jvav.SukebeiUtil(proxy_addr=args.proxy).get_av_by_id(
                    id=args.av2, is_nice=args.nc, is_uncensored=args.uc
                )
            )
        elif args.tp:
            self.handle_code(*jvav.DmmUtil(proxy_addr=args.proxy).get_top_stars(1))
        elif args.sr != "" or args.srn != "":
            star_name = args.sr if args.sr != "" else args.srn
            flag_srn = True if args.srn != "" else False
            if langdetect.detect(star_name) != "ja":  # zh
                wiki_json = jvav.WikiUtil(proxy_addr=args.proxy).get_wiki_page_by_lang(
                    topic=star_name, from_lang="zh", to_lang="ja"
                )
                if wiki_json and wiki_json["lang"] == "ja":
                    star_name = wiki_json["title"]
            if not flag_srn:
                self.handle_code(
                    *jvav.DmmUtil(proxy_addr=args.proxy).get_nice_avs_by_star_name(
                        args.sr
                    )
                )
            else:
                self.handle_code(
                    *jvav.JavBusUtil(proxy_addr=args.proxy).get_new_ids_by_star_name(
                        args.srn
                    )
                )
        elif args.pv1 != "":
            self.handle_code(
                *jvav.DmmUtil(proxy_addr=args.proxy).get_pv_by_id(args.pv1)
            )
        elif args.pv2 != "":
            self.handle_code(
                *jvav.AvgleUtil(proxy_addr=args.proxy).get_pv_by_id(args.pv2)
            )
        else:
            self.parser.print_help()


def main():
    parser = JvavArgsParser()
    parser.parse()
    parser.exec()


# pyinstaller --onefile cmd.py --name jvav # to build an exe named jvav.exe
# python -m jvav.cmd
if __name__ == "__main__":
    main()

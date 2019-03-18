# -*- coding:utf-8 -*-
#   AUTHOR: 张耘健
#     DATE: 2018-12-13
#     DESC: 获取线上全量GearBest商品详情
#           运行时间大约12小时
#           结果保存在good_data目录下
#           全量商品数据大约4GB左右

import time
import elasticsearch
import pandas as pd
from elasticsearch import helpers
from traceback import format_exc as excp_trace
from log_handler.Log import log_handler
from foundation.utils import *
from foundation.file_path import *

MILE_STONE = 100000


class GoodssnAllHandler(object):
    def __init__(self, features):
        self.features = features
        self.result_dict = dict()
        self.reset_result_dict()
        es_servers = read_es_config("ESEARCH")
        self.es_client = elasticsearch.Elasticsearch(
            hosts=es_servers
        )

    def reset_result_dict(self):
        for feature in self.features:
            self.result_dict[feature] = []

    def search(self, index='GB'):
        es_search_options = self.set_search_optional()
        es_result = self.get_search_result(es_search_options, index)
        goodssn_set = set()
        sku_counter = 0
        batch_counter = 0
        for item in es_result:
            try:
                good_dict = item["_source"]
                if good_dict["goodsSn"] not in goodssn_set:
                    goodssn_set.add(good_dict["goodsSn"])
                else:
                    continue
                for feature in self.features:
                    _ = good_dict[feature]
                for feature in self.features:
                    self.result_dict[feature].append(good_dict[feature])
                sku_counter += 1
                if sku_counter >= MILE_STONE:
                    final_result = pd.DataFrame(self.result_dict)
                    pd.to_pickle(final_result, get_good_data_path()+GOODS_INFO_FILE % batch_counter)
                    log_handler.log.info("Good data file %s downloaded..." % (GOODS_INFO_FILE % batch_counter))
                    batch_counter += 1
                    sku_counter = 0
                    self.reset_result_dict()
            except:
                pass

        if self.result_dict["goodsSn"]:
            final_result = pd.DataFrame(self.result_dict)
            pd.to_pickle(final_result, get_good_data_path()+GOODS_INFO_FILE % (batch_counter + 1))
            log_handler.log.info("Good data file %s downloaded..." % (GOODS_INFO_FILE % (batch_counter + 1)))

    def get_search_result(self, es_search_options, index2, scroll='1m', preserve_order=True):
        es_result = helpers.scan(
            client=self.es_client,
            query=es_search_options,
            scroll=scroll,
            index=index2,
            doc_type='sku',
            preserve_order=preserve_order
        )
        return es_result

    def set_search_optional(self):
        # 检索选项
        es_search_options = {
            "query": {
                "match_all": {}
            },
            "_source": self.features
        }
        return es_search_options

    def build_goods(self):
        self.search()


def build_goods_info():
    try:
        log_handler.log.info("----------------Building goods info----------------")
        features = [
            "goodsSn",
            "brandName",
            "categories",
            "discount",
            "shopPrice",
            "displayPrice",
            "stockFlag",
            "youtube",
            "totalFavoriteCount",
            "passTotalNum",
            "passAvgScore",
            "exposureSalesRate",
            "grossMargin",
            "exposureSalesVolume",
            "week2Sales",
            "week2SalesVolume",
            "dailyRate",
            "yesterdaySales",
            "goodsWebSpu"
        ]
        data_handler = GoodssnAllHandler(features)
        data_handler.build_goods()
        time.sleep(10)   # 睡眠10秒以等待商品列表已成功写入磁盘
    except Exception:
        log_handler.log.info("----------------Error building goods info----------------")
        log_handler.log.info(str(excp_trace()))
        raise Exception


if __name__ == '__main__':
    build_goods_info()

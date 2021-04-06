#!/usr/bin/env python3

import time
from authproxy import AuthServiceProxy
import tweepy
import random
import urllib.request
import json
import re
import sys

# Requires running Core RPC server on standard mainnet RPC port
if len(sys.argv) < 7:
    raise Exception('feeloop.py <RPC username> <RPC password> <oauth1> <oauth2> <token1> <token2>')

while True:
    bitcoin_req = "http://"+sys.argv[1]+":"+sys.argv[2]+"@127.0.0.1:8332"
    bitcoin = AuthServiceProxy(bitcoin_req)

    def get_rounded_feerate(result):
        rate = str(int(result*1000000)/10.0)+" sat/byte "
        if len(re.split("\.", rate)[0]) == 1:
            rate = " "+rate
        return rate

    try:
        mempool_info = bitcoin.getmempoolinfo()
        nextblock = ["Next: ", bitcoin.estimatesmartfee(1, "ECONOMICAL")["feerate"]]
        hour = ["1h:   ", bitcoin.estimatesmartfee(6, "ECONOMICAL")["feerate"]]
        six_hours = ["6h:   ", bitcoin.estimatesmartfee(6*6, "ECONOMICAL")["feerate"]]
        twelve_hours = ["12h:  ", bitcoin.estimatesmartfee(6*12, "ECONOMICAL")["feerate"]]
        day = ["1d:   ", bitcoin.estimatesmartfee(144, "ECONOMICAL")["feerate"]]
        half_week = ["3d:   ", bitcoin.estimatesmartfee(int(144*3.5), "ECONOMICAL")["feerate"]]
        week = ["1wk:  ", bitcoin.estimatesmartfee(144*7, "ECONOMICAL")["feerate"]]
        mem_min = ["Min:  ", mempool_info["mempoolminfee"]]

        bitstampprice = urllib.request.urlopen("https://www.bitstamp.net/api/v2/ticker/btcusd/").read()
        latest_price = float(json.loads(bitstampprice)["last"])
        price_for_250 = latest_price/4 # Price for 250 byte tx

        tweet = ""
        for estimate in [nextblock, hour, six_hours, twelve_hours, day, half_week, week, mem_min]:
            tweet += estimate[0]+get_rounded_feerate(estimate[1]) + " ${:0.2f}".format(round(price_for_250*float(estimate[1]),2))+"\n"

        count_str = f"{bitcoin.getblockcount():,d}"
        tweet += "Block height: "+ count_str+"\n"
        tweet += "Mempool depth: "+str(int(mempool_info["bytes"]/1000/1000))

    except Exception as e:
        print("Couldn't estimate. Sleeping: {}".format(str(e)))
        time.sleep(3600)
        continue

    print("Getting tweepy auth")
    # See http://docs.tweepy.org/en/latest/
    auth = tweepy.OAuthHandler(sys.argv[3], sys.argv[4])
    auth.set_access_token(sys.argv[5], sys.argv[6])
    api = tweepy.API(auth)

    try:
        api.update_status(tweet)
        print(tweet)
        blockcount = bitcoin.getblockcount()
        if blockcount % 15 == 0:
            print("Shilling.")
            try:
                tweet2 = "Tip me!\n\nhttps://tippin.me/@CoreFeeHelper\n\n{}".format(blockcount)
                api.update_status(tweet2)
                print("\n"+tweet2+"\n")
            except Exception as e:
                print("Error: "+str(e))
                pass

    except tweepy.TweepError as err:
        print("Error: "+str(err))
        print(tweet)
        print("------------------")
        pass


    time.sleep(3600)

"""ytsearch candidates for EP03 footage -> footage/cands.json (title, id, duration, channel)"""
import json, sys
from pathlib import Path
import yt_dlp
Q = {
 "attorney": ["변호인 2013 명장면", "변호인 송강호 법정 장면", "The Attorney 2013 trailer Song Kang-ho"],
 "roh_doc": ["노무현입니다 예고편", "무현 두 도시 이야기 예고편", "노무현 다큐멘터리 일대기"],
 "roh_young": ["노무현 변호사 시절 영상", "노무현 청문회 스타 1988 5공 청문회 명패"],
 "roh_busan": ["바보 노무현 2000년 부산 낙선", "노사모 결성 2000 노무현"],
 "ad2002": ["노무현의 눈물 광고 상록수 2002", "노무현 대선 광고 2002 눈물"],
 "bexco2002": ["노무현 문재인을 친구로 두고 있다 연설", "노무현 나는 대통령감이 됩니다 문재인 친구"],
 "roh_win": ["2002 대선 노무현 당선 순간", "노무현 대통령 취임식 2003"],
 "bongha": ["노무현 봉하마을 자전거 손녀", "노무현 야 기분 좋다 봉하 귀향 2008"],
 "probe2009": ["노무현 검찰 출석 2009 대검 버스", "노무현 대검 포토라인 2009년 4월 30일", "논두렁 시계 보도 국정원 2017 뉴스"],
 "death2009": ["노무현 서거 2009 뉴스 속보", "노무현 국민장 노제 서울광장 2009", "노무현 영결식 문재인"],
 "moon_young": ["문재인 특전사 사진 젊은 시절", "문재인 인권변호사 부산 시절 다큐"],
 "unmyeong": ["문재인의 운명 출간 2011", "문재인 운명 북콘서트"],
 "moon2012": ["문재인 2012 대선 패배 승복 연설", "문재인 2012 대선 유세"],
 "moon2015": ["문재인 당대표 2015 안철수 탈당", "더불어민주당 2016 총선 결과 제1당"],
 "candle": ["촛불집회 2016 광화문 드론", "박근혜 탄핵 인용 2017 3월 10일 헌재"],
 "moon2017": ["문재인 대통령 당선 2017 5월 9일 광화문", "문재인 대통령 취임 2017"],
 "memorial2017": ["문재인 대통령 노무현 8주기 추도사 전문", "노무현 8주기 추도식 2017 문재인"],
 "nis2017": ["국정원 개혁위 노무현 망신주기 2017 뉴스", "원세훈 노무현 논두렁 시계 국정원 개입 뉴스"],
 "mb2018": ["이명박 정치보복 성명 2018 1월 17일", "문재인 분노 이명박 노무현 죽음 2018", "이명박 구속 2018 3월 22일 뉴스", "이명박 징역 17년 확정 2020"],
 "bongha2022": ["문재인 봉하마을 2022 추도식 약속 지켰다", "노무현 13주기 문재인 참석"],
 "scenery": ["봉하마을 드론", "낙동강 드론 4K", "부산 야경 드론 4K", "한강 드론 4K 일출"],
 "bgm": ["상록수 피아노", "상록수 연주곡", "변호인 OST", "노무현 추모곡 피아노"],
}
out = {}
opts = {"quiet": True, "extract_flat": True, "skip_download": True, "no_warnings": True}
with yt_dlp.YoutubeDL(opts) as y:
    for k, qs in Q.items():
        out[k] = []
        for q in qs:
            try:
                r = y.extract_info(f"ytsearch8:{q}", download=False)
                for e in r.get("entries") or []:
                    out[k].append({"q": q, "id": e.get("id"), "title": e.get("title"), "dur": e.get("duration"), "ch": e.get("channel") or e.get("uploader")})
            except Exception as ex:
                out[k].append({"q": q, "err": str(ex)[:200]})
        print(k, len(out[k]), flush=True)
Path("footage").mkdir(exist_ok=True)
Path("footage/cands.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("FIND_DONE")

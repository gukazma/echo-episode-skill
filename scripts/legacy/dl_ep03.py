"""download selected EP03 footage -> footage/<key>.mp4 (<=1080p)"""
import subprocess, sys
from pathlib import Path
L = """att_trailer4k N20t9VACwQc
att_scene1 w7zRZskNfEs
att_scene2 q6yJ5Fk7uKk
att_scene3 cO-H-HY3_oI
att_burim Xa8MF5i6uLI
roh_found_doc 0hXW-HdK4tA
roh_kbs60 m1EiuTjPyE4
roh_kbs3days 7S2tXi4QZx4
roh_iam_trailer Dnxicj7blX4
roh_twocities_trailer 7-HnhodmJm4
roh_lawyer G-a11KcYICU
roh_hearing 7SG07dVR4M8
roh_hearing2 ZFKzlpaYB44
roh_nameplate bD-D4JDI1PM
roh_2000 DMAV226QXvY
roh_2000_loss 8lSjocaRks0
ad_tears iuMpZtx2EKc
ad_evergreen JOuTgtGCCts
bexco2002 EEfGAeJXJ2Q
roh_win2002 e3Y4w01SK2o
roh_inaug XrIAfHQW-ck
bongha_bike 7qwA2f-iHBo
bongha_feelgood qDRTDQ1GS6A
probe_bus scVed093ZL4
probe_jtbc lcI4PNaypc4
nis_watch_ytn fbDv1kP6wgE
nis_sbs lPlnurpHeO0
nis_won PNQMovl3QjQ
nis_lee2018 S7eyR8iLpmA
death_kbs OSebCdqPSNc
death_plaza zc9-CqNMbq4
funeral_baek sQi481vsbaA
funeral_rite OWnkV2WIcy8
moon_reads_will JHGc8gtreq0
moon_promo FUVWmQGXq4c
moon_kbs_life 77_qiojmbCg
moon_ytn_life BCfSPakZ4mA
moon_book_concert Gyn7HP6vel0
moon2012_concede V33On3f0zVs
moon2012_tears hXH7I0DP31Q
moon2015_ahn -Hy8YvmNcFc
moon2016_first BTXXr686QFU
candle_million 7ErqETqiK6s
candle_drone JOjM2Rkvz4U
candle_impeach 2x6uhLoArEE
moon2017_win 68op2U6bGgg
moon2017_oath DSiHWrf2xwg
moon2017_inaug xBj8QOTbjPQ
memorial2017 7BWuOFvusyM
nis2017_ytn kSCFz4Baibs
mb_statement CsaMZzg1tH0
moon_furious TdQqL1XrbfY
moon_furious_kbs hxuybGRzweo
mb_arrest 58somV3y_HU
mb_17y VP6FZVaDnDU
bongha2022 k0F68foZ6uQ
bongha2022_mbn wJi40D-NPXo
bongha_drone MPTajcoGgq0
bongha_4k IKxILwIkeLs
river_nakdong MOUL94w3Zj8
river_andong WyU5wBVumko
busan_drone cSi-uJ8YErk
busan_night X8m8ReXVXls
impeach_reject PQXUP95r_ME
impeach_vote qmnA-APTWi4
impeach_court JfccxbVCdfw
frugal_noodle PSF8zPIy70E
frugal_cafeteria 2TXzFXnnPlk
frugal_own_money Hnl2DQg4DqM
frugal_coffee 0n9nHZOig-g
moon_inaug_speech -7z1HE03Oas
roh_citizens GDU8KYHpjsE
moon_people_first hJXaNVtfooI
june1987_busan NaV8s6X3KAk
moon_minjeong 1qAwqHZ5fSI
pyeongsan_book eZgR1-DMKmI
pyeongsan_home YDHb4Do6wMw
jeju43_found 75KTFFhbFqE
jeju43_apology dc3UDT4U4QQ
mdl2007_hani xxXIo81Vwkg
mdl2007_actor mt6WzeNAiak
prosecutors2003 54OZLhTbevQ
prosecutors2003b LKueuEa11bM
sejong_aerial SJ9kc5Gb1cU
sejong_4k jNF10KDAFjo
gwangju2002 9uZODD-qF4k
gwangju2002_kbs UBF-HtXw9bo
river_song bnXXg_c6IXU
river_guest _QPYHy70FmM
roh_ideal rVBYIkUM1Ig
mdl2018_sbs 3VcxLzUe0tM
moon_yeomin pcO55UVFLyM
moon_wage ytsearch1:최저임금 16.4% 인상 7530원 결정 2018 뉴스
moon_52h ytsearch1:주52시간 근무제 시행 2018년 7월 1일 뉴스
moon_care ytsearch1:문재인 케어 발표 2017 서울성모병원 문재인 대통령
moon_wage_sorry ytsearch1:문재인 대통령 최저임금 1만원 공약 못지켜 송구 2018 7월
ljy_arrest ytsearch1:이재용 구속 2017년 2월 17일 뉴스 삼성 총수 첫 구속
ksj_ftc ytsearch1:김상조 공정거래위원장 임명 재벌 저격수 2017 뉴스
ljy_parole ytsearch1:이재용 가석방 출소 2021년 8월 13일 서울구치소 뉴스
capital_ruling rkfc7YbVYgw
card_crisis 5BQb8Fa872U
market_power O3IWVgbCspE
june1987_kbsbusan Nk9urkzyDcw
home2008_miryang G8YUBzM-_oE
home2008_3days -y41HUxTkag
watch_sbs2009 XwCQ47fFxvk
watch_mbc 3RyKjSOh6t4
roh_success DC045FTHC4s
roh_camera iCg1zypvPE8
roh_office_daejeon nvBba8mLV2E
roh_marines PX42KorPpEA
roh_smiles wmt5TJeN19Y
nsa_hunger2004 HLqLbWod53c
uri_win2004 ikM3IjIgwoQ
roh_newyear_short 7kMhlO_yrnY"""
B = """bgm_evergreen_viola 211FIFNDqa8
bgm_evergreen_piano 8-jBk0ljFqs
bgm_evergreen_piano2 lVKZ94FsSII
bgm_attorney_99 8iWmJOOTqns
bgm_attorney_painful NjlAC03iNn4
bgm_attorney_suite qVqQwnbk6jg
bgm_evergreen_ensemble ia_qPWAF8-c"""
ep = Path(__file__).resolve().parent
for block, sub, audio in ((L, "footage", False), (B, "bgm_src", True)):
    (ep / sub).mkdir(exist_ok=True)
    for line in block.split("\n"):
        k, vid = line.split(maxsplit=1)
        out = ep / sub / (f"{k}.m4a" if audio else f"{k}.mp4")
        if out.exists():
            continue
        fmt = ["-f", "ba[ext=m4a]/ba"] if audio else ["-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b", "--merge-output-format", "mp4"]
        r = subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", *fmt, "-o", str(out), (vid if vid.startswith("ytsearch") else f"https://www.youtube.com/watch?v={vid}")])
        print(k, "ok" if out.exists() else f"FAIL {r.returncode}", flush=True)
print("DL_DONE", flush=True)

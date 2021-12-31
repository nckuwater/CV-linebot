# TOC project - CV linebot
## 介紹
可以提供即時線上影像處理功能的Line bot,    
讓使用者用手機也可以做到基本的圖片處理，  
主要使用opencv開發。

### 開發環境
作業系統 - windows10  
使用語言 - python 3.8

### 主要功能
* 去除圖片背景 (有選區塊的功能)
* 高斯模糊 (可用於去除圖片雜訊)
* 雙邊濾波 (Bilateral filter, 能平滑圖片且保留較完整的線條)
* 灰階化

有提供按鈕選項的功能(輸入'help')

## 建構環境
**需使用Anaconda安裝部分套件避免錯誤**  
先安裝requirement.txt的內容  
`pip install -r requirement.txt`

其中pygraphviz  會出錯, 需使用anaconda安裝  
`conda install -c alubbock pygraphviz`

而裝完之後又會遇到graphviz的內部問題 (例如找不到AGraph.h或graphviz libs)  
則需安裝python-graphviz  
`pip install python-graphviz`  

需配置以下本地檔案
* 創建.env 並且設定
    1. LINE_CHANNEL_SECRET=...
    2. LINE_CHANNEL_ACCESS_TOKEN=...
    3. PORT=...
    4. base_url=https... 就是伺服器的url(尾端沒有\\)

* 創建資料夾  
    ./static/images 用來存放運行時的圖片

## 使用範例

輸入 'help' 可以有按鈕指令選項，點擊就可以使用指令。  
輸入 'state' 可以顯示目前state。  
* 去除圖片背景  
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/rbg1.png?raw=true)
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/rbg2.png?raw=true)
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/rbg3.png?raw=true)  

* 高斯模糊  
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/gau1.png?raw=true)
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/gau2.png?raw=true)  

* 平滑圖片 (bilateral)  
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/bil1.png?raw=true)
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/example/bil2.png?raw=true)

## State架構圖
![alt text](https://github.com/nckuwater/CV-linebot/blob/master/fsm.png?raw=true)

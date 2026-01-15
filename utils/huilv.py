import requests


def convert_cny_to_tzs(amount_cny):
    """
    查詢當前匯率並將人民幣 (CNY) 轉換為坦桑尼亞先令 (TZS)。
    使用無需 Key 的公開 API: open.er-api.com
    """

    # API 地址，直接請求 CNY 的數據
    api_url = "https://open.er-api.com/v6/latest/CNY"

    print(f"正在查詢匯率 (基礎貨幣: CNY)...")

    try:
        # 發送請求
        response = requests.get(api_url, timeout=10)
        data = response.json()

        # 檢查請求是否成功
        if data.get('result') == 'success':
            # print(data['rates'])
            # 獲取 TZS 的匯率
            rate = data['rates'].get('AOA')

            if rate:
                # 進行轉換計算
                amount_tzs = amount_cny * rate
                last_update = data.get('time_last_update_utc', '未知')

                print("-" * 30)
                print(f"匯率更新時間 (UTC): {last_update}")
                print(f"當前匯率: 1 CNY = {rate:,.2f} TZS")
                print("-" * 30)
                print(f"轉換結果:")
                print(f"{amount_cny:,.2f} 人民幣 (CNY)")
                print(f"   ↓↓↓")
                print(f"{amount_tzs:,.2f} 坦桑尼亞先令 (TZS)")
                print("-" * 30)
                with open('./huilv.txt', 'w+', encoding='utf-8') as f:
                    f.write(f"{amount_tzs:,.2f}")
                return amount_tzs
            else:
                print("錯誤: 數據中未找到 TZS 的匯率。")
        else:
            print("錯誤: API 請求未成功。")

    except requests.exceptions.RequestException as e:
        print(f"網絡錯誤: {e}")
    except Exception as e:
        print(f"發生未知錯誤: {e}")


if __name__ == "__main__":
    # 在這裡輸入您想要兌換的人民幣金額
    my_cny_amount = 1  # 例如 100 元人民幣
    convert_cny_to_tzs(my_cny_amount)

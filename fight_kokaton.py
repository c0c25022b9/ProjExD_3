import math  # ★演習4：角度計算のために追加
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # ★演習4：初期の向き（右向き）を定義

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # ★演習4：合計移動量が0でない時、向きを更新
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        こうかとんの向きに応じてビームの速度、角度、初期位置を設定する（演習4）
        """
        # 1. こうかとんの向いている方向を速度(vx, vy)に代入
        self.vx, self.vy = bird.dire

        # 2. 直交座標から極座標の角度に変換し、画像を回転させる
        theta = math.atan2(-self.vy, self.vx)
        angle = math.degrees(theta)
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, 1.0)
        
        self.rct = self.img.get_rect()
        
        # 3. こうかとんの向きを考慮した初期位置の計算
        self.rct.centerx = bird.rct.centerx + (bird.rct.width * self.vx // 5)
        self.rct.centery = bird.rct.centery + (bird.rct.height * self.vy // 5)

    def update(self, screen: pg.Surface):
        """
        ビームを移動させる
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        爆弾円Surfaceを生成する
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を移動させる
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """
    打ち落とした爆弾の数を表示するスコアに関するクラス（演習1）
    """
    def __init__(self):
        self.fonto = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス（演習3）
    """
    def __init__(self, bomb: Bomb):
        img_orig = pg.image.load("fig/explosion.gif")
        img_flip = pg.transform.flip(img_orig, True, True)
        self.imgs = [img_orig, img_flip]
        self.rct = img_orig.get_rect()
        self.rct.center = bomb.rct.center
        self.life = 20  # 爆発の表示フレーム数

    def update(self, screen: pg.Surface):
        self.life -= 1
        if self.life > 0:
            img_idx = (self.life // 5) % 2  # チラつき防止で交互に表示
            screen.blit(self.imgs[img_idx], self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    
    beams = []        # 演習2：複数のビームを管理するリスト
    explosions = []   # 演習3：爆発エフェクトを管理するリスト
    score = Score()   # 演習1：スコアのインスタンス
    
    # ゲームオーバー表示用のフォントとSurfaceを準備
    go_font = pg.font.Font(None, 100)                     # 大きめのフォントを設定
    go_img = go_font.render("GAME OVER", True, (255, 0, 0)) # 赤色の文字で生成
    go_rct = go_img.get_rect()
    go_rct.center = (WIDTH // 2, HEIGHT // 2)             # 画面の真ん中に座標を合わせる
    
    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # 演習2：スペースキーでビーム追加
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # 1. こうかとんと全ての爆弾の衝突判定（ゲームオーバー処理）
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)      # こうかとんが泣く画像に切り替え
                screen.blit(go_img, go_rct)     # 画面中央に「GAME OVER」の文字を描画
                pg.display.update()             # 画面に即座に反映させる
                time.sleep(2)                   # 2秒間そのままフリーズして見せる
                return                          # ゲーム終了
        
        # 2. ビームと爆弾の衝突判定
        for j, beam in enumerate(beams):
            for i, bomb in enumerate(bombs):
                if beam is not None and bomb is not None:
                    if beam.rct.colliderect(bomb.rct):
                        explosions.append(Explosion(bomb))  # 演習3：爆発エフェクト生成
                        score.score += 1                    # 演習1：スコア加算
                        beams[j] = None
                        bombs[i] = None
                        bird.change_img(6, screen)          # 喜ぶエフェクト
                        pg.display.update()

        # 3. 画面外に出たビームの削除判定
        for j, beam in enumerate(beams):
            if beam is not None:
                yoko, tate = check_bound(beam.rct)
                if not yoko or not tate:  # ★演習4：上下左右どちらかの画面外に出たら消去
                    beams[j] = None

        # 4. リストのクリーンアップ
        bombs = [bomb for bomb in bombs if bomb is not None]
        beams = [beam for beam in beams if beam is not None]
        explosions = [exp for exp in explosions if exp.life > 0]

        # 5. 各オブジェクトの描画更新
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        for bomb in bombs:
            bomb.update(screen)
            
        for beam in beams:
            beam.update(screen)
            
        for exp in explosions:
            exp.update(screen)
            
        score.update(screen)
         
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
import fitz
import cv2
import numpy as np

def remove_faint_watermark(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    out_doc = fitz.open()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 提高分辨率到 4 倍，让水印边缘更清晰，方便识别
        pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
        
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4: 
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3: 
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
        # 统一转灰度图处理，水印和文字的区别就在于“灰度”深浅
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # --- 核心逻辑：保护黑字，剔除灰水印 ---
        # 1. 设置阈值。纯黑色的字灰度是 0，水印因为半透明，灰度通常在 200 以上
        # 我们把灰度值在 180 到 250 之间的（也就是浅灰、极淡的红色）抠出来
        # （白底是 255，所以上限设为 250）
        _, mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        # 2. 将挑出来的水印区域涂成纯白
        img[mask == 255] = [255, 255, 255]
        
        # --- 进阶修补：如果你还有残留的灰色边缘 ---
        # 我们用形态学膨胀一下，把抠出来的白色区域稍微扩大一点，完全覆盖半透明的残影
        kernel = np.ones((2,2), np.uint8)
        img_cleaned = cv2.dilate(img, kernel, iterations=1)
        # 膨胀会导致黑字变粗，如果你介意，可以跳过上面两行，直接用 img
        
        # 将处理后的图片写回 PDF
        is_success, buffer = cv2.imencode(".png", img) # 用原图，不膨胀
        if is_success:
            img_bytes = buffer.tobytes()
            rect = page.rect
            new_page = out_doc.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=img_bytes)
            
    out_doc.save(output_pdf, garbage=4, deflate=True)
    out_doc.close()
    doc.close()
    print("清理完毕，请查看 output.pdf")

remove_faint_watermark("01.pdf", "44444.pdf")
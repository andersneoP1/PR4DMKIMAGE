import os
import time
import asyncio
import multiprocessing
from PIL import Image, ImageDraw

# Конфигурационные параметры
img_src = "source_images"
img_out = "processed"
total_pics = 20
new_resolution = (800, 600)


def transform_photo(input_path, output_path):
    pic = Image.open(input_path)
    
    # 90 градусов по часовой стрелке
    rotated_pic = pic.transpose(Image.ROTATE_270)
    
    # Ресайз до 800х600
    resized_pic = rotated_pic.resize(new_resolution, resample=Image.LANCZOS)
    
    # Превращаем в оттенки серого
    grayscale_pic = resized_pic.convert("L")
    
    grayscale_pic.save(output_path, "JPEG")


def clean_folder():
    if not os.path.exists(img_out):
        os.makedirs(img_out)
    else:
        for f in os.listdir(img_out):
            if f.startswith("out_") and f.endswith(".jpg"):
                os.remove(os.path.join(img_out, f))


def make_source_images():
    if not os.path.exists(img_src):
        os.makedirs(img_src)
        print(f"[Старт] Создана папка: {img_src}")

    already_done = [f for f in os.listdir(img_src) if f.endswith(".jpg")]
    if len(already_done) == total_pics:
        print("[Старт] Набор картинок уже подготовлен.")
        return

    print(f"[Старт] Генерируем {total_pics} изображений для теста...")
    for idx in range(total_pics):
        img_file = os.path.join(img_src, f"img_{idx}.jpg")
        
        # Создаем изображение с фиолетовым фоном
        pic = Image.new("RGB", (1600, 1200), color=(60, 45, 70))
        draw = ImageDraw.Draw(pic)

        # Рисуем круговую мишень и сетку
        for radius in range(100, 1000, 120):
            outline_color = (150, (idx * 15 + radius // 5) % 256, (255 - radius // 4) % 256)
            draw.ellipse(
                [(800 - radius // 2, 600 - radius // 2), (800 + radius // 2, 600 + radius // 2)],
                outline=outline_color,
                width=4
            )
            draw.line([(0, 600), (1600, 600)], fill=(100, 100, 120), width=2)
            draw.line([(800, 0), (800, 1200)], fill=(100, 100, 120), width=2)

        # Добавляем текстовый ярлык
        draw.text((60, 60), f"Item ID: {idx}", fill=(240, 240, 240))
        
        pic.save(img_file, "JPEG", quality=90)
    print("[Старт] Картинки созданы!\n")


def sequential_process(files):
    clean_folder()
    start = time.perf_counter()
    for name in files:
        src = os.path.join(img_src, name)
        dest = os.path.join(img_out, f"out_{name}")
        transform_photo(src, dest)
    return time.perf_counter() - start


def multiprocess_worker(args):
    source, target = args
    transform_photo(source, target)


def multiprocess_pool(files):
    clean_folder()
    
    # Создаем пары путей
    work_items = []
    for name in files:
        src = os.path.join(img_src, name)
        dest = os.path.join(img_out, f"out_{name}")
        work_items.append((src, dest))
        
    start = time.perf_counter()
    cores = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=cores) as pool:
        pool.map(multiprocess_worker, work_items)
    return time.perf_counter() - start


async def async_runner(files):
    tasks = []
    for name in files:
        src = os.path.join(img_src, name)
        dest = os.path.join(img_out, f"out_{name}")
        # Запускаем напрямую через to_thread в цикле
        tasks.append(asyncio.to_thread(transform_photo, src, dest))
    await asyncio.gather(*tasks)


def async_concurrency(files):
    clean_folder()
    start = time.perf_counter()
    asyncio.run(async_runner(files))
    return time.perf_counter() - start


def main():
    make_source_images()
    
    pic_list = sorted([name for name in os.listdir(img_src) if name.startswith("img_") and name.endswith(".jpg")])
    if not pic_list:
        print("Ошибка: Тестовые файлы отсутствуют!")
        return

    print("=== Начало сравнительных тестов ===")
    
    print("Выполнение: Последовательный алгоритм...")
    seq_time = sequential_process(pic_list)
    print(f"Последовательный режим: {seq_time:.4f} с.")
    
    print("Выполнение: Мультипроцессорный Pool...")
    mp_time = multiprocess_pool(pic_list)
    print(f"Мультипроцессорный режим: {mp_time:.4f} с.")
    
    print("Выполнение: Асинхронный asyncio...")
    async_time = async_concurrency(pic_list)
    print(f"Асинхронный режим: {async_time:.4f} с.\n")
    
    print("--------------------------------------------------")
    print("                РЕЗУЛЬТАТЫ АНАЛИЗА                ")
    print("--------------------------------------------------")
    print(f"Количество файлов   : {len(pic_list)} шт.")
    print(f"Конечный формат     : 800x600, Lanczos, Grayscale")
    print("--------------------------------------------------")
    print(f"1. Последовательно  : {seq_time:.4f} с.")
    print(f"2. Пул процессов    : {mp_time:.4f} с. (Ускорение: {seq_time / mp_time:.2f}x)")
    print(f"3. Асинхронно (GIL) : {async_time:.4f} с. (Ускорение: {seq_time / async_time:.2f}x)")
    print("--------------------------------------------------")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

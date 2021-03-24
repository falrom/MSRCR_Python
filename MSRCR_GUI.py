import tkinter as tk
import numpy as np
import os
import cv2
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from PIL import Image, ImageTk


def retinex_scales_distribution(max_scale, nscales):
    scales = []
    scale_step = max_scale / nscales
    for s in range(nscales):
        scales.append(scale_step * s + 2.0)
    return scales


def CR(im_ori, im_log, alpha=128., gain=1., offset=0.):
    im_cr = im_log * gain * (
            np.log(alpha * (im_ori + 1.0)) - np.log(np.sum(im_ori, axis=2) + 3.0)[:, :, np.newaxis]) + offset
    return im_cr


def MSRCR(image, max_scale, nscales, dynamic=2.0, do_CR=True):

    im_ori = np.float32(image)
    if (im_ori.ndim == 2):
        im_ori = im_ori[:, :, np.newaxis]
    if (im_ori.shape[2] == 1):
        im_ori = im_ori.repeat(3, axis=2)

    scales = retinex_scales_distribution(max_scale, nscales)

    im_blur = np.zeros([len(scales), im_ori.shape[0], im_ori.shape[1], im_ori.shape[2]])
    im_mlog = np.zeros([len(scales), im_ori.shape[0], im_ori.shape[1], im_ori.shape[2]])

    for channel in range(3):
        for s, scale in enumerate(scales):
            # If sigma==0, it will be automatically calculated based on scale
            im_blur[s, :, :, channel] = cv2.GaussianBlur(im_ori[:, :, channel], (0, 0), scale)
            im_mlog[s, :, :, channel] = np.log(im_ori[:, :, channel] + 1.) - np.log(im_blur[s, :, :, channel] + 1.)

    im_retinex = np.mean(im_mlog, 0)
    if do_CR:
        im_retinex = CR(im_ori, im_retinex)

    im_rtx_mean = np.mean(im_retinex)
    im_rtx_std = np.std(im_retinex)
    im_rtx_min = im_rtx_mean - dynamic * im_rtx_std
    im_rtx_max = im_rtx_mean + dynamic * im_rtx_std

    im_rtx_range = im_rtx_max - im_rtx_min

    im_out = np.uint8(np.clip((im_retinex - im_rtx_min) / im_rtx_range * 255.0, 0, 255))

    return im_out


top = tk.Tk()
top.title('MSRCR')
top_source = None
top_output = None


def set_None_top_source():
    global top_source
    top_source.destroy()
    top_source = None


def set_None_top_output():
    global top_output
    top_output.destroy()
    top_output = None


label_source = None
label_output = None

img_source = None
pimg_source = None
img_output = None
pimg_output = None
do_CR = tk.BooleanVar()

scale_max_scale = tk.Scale(top, label='max scale:', from_=50, to=500, orient=tk.HORIZONTAL, length=300)
scale_nscales = tk.Scale(top, label='nscales:', from_=1, to=8, orient=tk.HORIZONTAL, length=300)
scale_dynamic = tk.Scale(top, label='dynamic:', from_=1, to=5, resolution=0.01, orient=tk.HORIZONTAL, length=300)
check_do_CR = tk.Checkbutton(top, text="do CR", variable=do_CR, onvalue=True, offvalue=False)

scale_max_scale.set(300)
scale_nscales.set(3)
scale_dynamic.set(2)
check_do_CR.select()


def open_img():
    global img_source
    global pimg_source
    global top_source
    global label_source

    img_path = askopenfilename()
    if os.path.exists(img_path):
        img_source = Image.open(img_path)
        pimg_source = ImageTk.PhotoImage(img_source)
        if top_source is None:
            top_source = tk.Toplevel()
            top_source.title('Source Image')
            top_source.protocol('WM_DELETE_WINDOW', set_None_top_source)
            label_source = tk.Label(top_source)
            label_source.pack()
        label_source.configure(image=pimg_source)


def do_MSRCR():
    global img_source
    global img_output
    global pimg_output
    global top_output
    global label_output

    if img_source is None:
        return
    print('max_scale:', scale_max_scale.get(), '  nscales:', scale_nscales.get(), '  dynamic:', scale_dynamic.get(),
          '  do_CR:', do_CR.get())
    img_output = Image.fromarray(
        MSRCR(np.array(img_source), scale_max_scale.get(), scale_nscales.get(), scale_dynamic.get(), do_CR.get()))
    pimg_output = ImageTk.PhotoImage(img_output)
    # print(top_output)
    if top_output is None:
        top_output = tk.Toplevel()
        top_output.title('Output Image')
        top_output.protocol('WM_DELETE_WINDOW', set_None_top_output)
        label_output = tk.Label(top_output)
        label_output.pack()
    top_output.deiconify()
    label_output.configure(image=pimg_output)


def do_save():
    global img_output
    # print(img_output)
    if img_output is None:
        return
    save_path = asksaveasfilename()
    # print(save_path)
    if save_path:
        img_output.save(save_path)


button_open = tk.Button(top, text='Open', command=open_img)
button_MSRCR = tk.Button(top, text='MSRCR', command=do_MSRCR)
button_save = tk.Button(top, text='Save as', command=do_save)

scale_max_scale.grid(row=0, column=0, columnspan=4)
scale_nscales.grid(row=1, column=0, columnspan=4)
scale_dynamic.grid(row=2, column=0, columnspan=4)
check_do_CR.grid(row=3, column=0)
button_open.grid(row=3, column=1)
button_MSRCR.grid(row=3, column=2)
button_save.grid(row=3, column=3)

top.mainloop()

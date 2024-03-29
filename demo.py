##################################################
# FILE: demo.py
# AUTHOR: SEAN TRONSEN (LANL)
#
# SUMMARY:
# The contents of this file are written with the intent to illustrate basic
# usage of the package utilities. By no means should it be expected to be
# comprehensive, but it provides a good foundation nonetheless.
#
# Should the reader have any questions, they are advised to first skim through
# the source code and read the inline documentation. For any questions that
# still remain, please get in touch with the author.
##################################################
##################################################

# OPTIONAL IMPORTS
import os

os.environ["VIEWER_PERF_LOG"] = "1"  # remove to disable performance logging


# STANDARD IMPORTS
import cv2
import numpy as np
from qtviewer import *
import sys
from demo_utils import *


def demo_image_viewer():
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = norm_uint8(cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY))

    # IMPORTANT: Expensive and avoidable computations should be completed prior for
    # best results. Slow rendering times result from a bottleneck in the code
    # written into a provided callback function.
    #
    # EXAMPLE: Compare the rendering speed for when the resize slider is moved
    # versus when the sigma parameter is updated (resize performs more
    # computation in this case, making it slower in comparison).
    img_test_small = img_test.copy()
    img_test = resize_by_ratio(img_test, 10)
    noise_image = np.random.randn(*(img_test.shape)).astype(np.int8)  # pyright: ignore

    # IMPORTANT: Ensure the kwargs parameter is specified to allow the function
    # interface to remain generic for top level controls and ignore extra
    # arguments without failing. To elaborate, parameters associated with
    # global control widgets are passed to the callbacks for all top level
    # display panes.
    def callback_0(rho, sigma, **_):
        resized = resize_by_ratio(img_test, rho)
        noise_slice = noise_image[: resized.shape[0], : resized.shape[1]]
        result = resized + (noise_slice * sigma)
        return result

    def callback_1(sigma, **_):
        noise_slice = noise_image[: img_test_small.shape[0], : img_test_small.shape[1]]
        result = img_test_small + (noise_slice * sigma)
        return result

    # define the viewer interface and run the application
    # happy tuning / visualizing!
    image_viewer = VisionViewer()
    trackbar_rho = ParameterTrackbar("rho", 0.001, 1, step=0.001, init=0.5)
    trackbar_sigma = ParameterTrackbar("sigma", 0, 100, 2)

    # set to False if panning and zoom should not reset on each new frame
    ip = ImagePane(callback_0, autoRange=True)
    ip2 = ImagePane(callback_1)
    image_viewer.add_mosaic([[ip, ip2], [trackbar_rho, trackbar_sigma]])
    image_viewer.run()


def demo_static_image_viewer():
    img_test = cv2.imread("sample-media/checkboard_non_planar.png").astype(np.uint8)
    img_test = norm_uint8(cv2.cvtColor(img_test, cv2.COLOR_BGR2GRAY))

    image_viewer = VisionViewer()
    ip = ImagePane(lambda **_: img_test)
    image_viewer.add_panes(ip)
    image_viewer.run()


def demo_plot_viewer():

    def callback(nsamples, sigma, omega, phasem, animation_tick, **_):
        cphase = (animation_tick / (2 * np.pi)) * phasem
        sinusoid = np.sin((np.linspace(0, omega * 2 * np.pi, nsamples) + cphase))
        noise = np.random.randn(nsamples)
        result = sinusoid + (noise[:nsamples] * sigma)
        waves = 3
        return np.array([result] * waves) + np.arange(waves).reshape(-1, 1)

    viewer = PlotViewer(title="Multiple Plots: A Visual Illustration of Signal Aliasing")
    trackbar_n = ParameterTrackbar("nsamples", 100, 1000, 100)
    trackbar_omega = ParameterTrackbar("omega", 1, 50, init=50)
    trackbar_sigma = ParameterTrackbar("sigma", 0, 3, 0.1)
    trackbar_phasem = ParameterTrackbar("phasem", 0.1, 10, 0.1, init=1)
    pl = Plot2DLinePane(callback, ncolors=3, cmap="plasma")
    pl.set_title("Signal Aliasing: Labeled Graph")
    pl.set_xlabel("Sample Number")
    pl.set_ylabel("Amplitude")
    pl = Animator(fps=60, contents=pl).animation_content
    ps = Animator(fps=60, contents=Plot2DScatterPane(callback)).animation_content
    viewer.add_mosaic([[pl, ps], [trackbar_n, trackbar_omega], [trackbar_phasem, trackbar_sigma]])
    viewer.run()


def demo_3d_prototype():

    def callback(animation_tick, sigma, **_):
        gaussian = cv2.getGaussianKernel(20, sigma=sigma)
        gaussian = gaussian * gaussian.T  # pyright: ignore
        return gaussian * ((animation_tick % 500) + 1) * 10

    viewer = PlotViewer()
    # viewer = PlotViewer(width=1600, height=900)
    # viewer.resize(2000, 1500)
    animator = Animator(fps=60, contents=Plot3DPane(callback))
    d3plot = animator.animation_content
    control_bar = AnimatorControlBar(animator=animator)
    t_sigma = ParameterTrackbar("sigma", 0.1, 25, step=0.1, init=5)
    viewer.add_panes(d3plot, control_bar, t_sigma)
    viewer.run()


if __name__ == "__main__":
    options = {}
    options[demo_image_viewer.__name__] = demo_image_viewer
    options[demo_static_image_viewer.__name__] = demo_static_image_viewer
    options[demo_plot_viewer.__name__] = demo_plot_viewer
    options[demo_3d_prototype.__name__] = demo_3d_prototype
    if len(sys.argv) >= 2:
        options[sys.argv[1]]()
    else:
        demo_3d_prototype()

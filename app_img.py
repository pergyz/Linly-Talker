import os
import gradio as gr
from zhconv import convert
from src.LLM import *
from src.Asr import OpenAIASR
from src.SadTalker import SadTalker 
from src.TTS import EdgeTTS
import time
import random 
from configs import *
description = """<p style="text-align: center; font-weight: bold;">
    <span style="font-size: 28px;">Linly 智能对话系统 (Linly-Talker)</span>
    <br>
    <span style="font-size: 18px;" id="paper-info">
        [<a href="https://zhuanlan.zhihu.com/p/671006998" target="_blank">知乎</a>]
        [<a href="https://www.bilibili.com/video/BV1rN4y1a76x/" target="_blank">bilibili</a>]
        [<a href="https://github.com/Kedreamix/Linly-Talker" target="_blank">GitHub</a>]
    </span>
    <br> 
    <span>Linly-Talker 是一款智能 AI 对话系统，结合了大型语言模型 (LLMs) 与视觉模型，是一种新颖的人工智能交互方式。</span>
</p>
"""

use_ref_video = False
ref_video = None
ref_info = 'pose'
use_idle_mode = False
length_of_audio = 5

def asr(audio):
    #sr, data = audio
    #audio = "audio_output.wav"
    #sf.write(audio, data, samplerate=sr)  # 以44100Hz的采样率保存为WAV文件
    #print(audio)
    question = openaiasr.transcribe(audio)
    question = convert(question, 'zh-cn')
    return question

def linly_response(question, voice = 'zh-CN-XiaoxiaoNeural'):
    #answer = llm.predict(question)
    answer = llm.generate(question)
    print(answer)
    os.system(f'edge-tts --text "{answer}" --voice {voice} --write-media answer.wav')
    #audio, sr = librosa.load(path='answer.wav')
    return 'answer.wav', answer

def llm_response(question, voice = 'zh-CN-XiaoxiaoNeural', rate = 0, volume = 100, pitch = 0):
    #answer = llm.predict(question)
    answer = llm.generate(question)
    print(answer)
    # 默认保存为answer.wav
    # 以前旧方法直接调用命令行
    # os.system(f'edge-tts --text "{answer}" --voice {voice} --write-media answer.wav')
    # 现在调用函数，其实两者皆可
    tts.predict(answer, voice, rate, volume, pitch , 'answer.wav', 'answer.vtt')
    # audio, sr = librosa.load(path='answer.wav')
    return 'answer.wav', 'answer.vtt', answer


def text_response(text, voice, rate, volume, pitch, source_image,
                    preprocess_type, 
                    is_still_mode,
                    enhancer,
                    batch_size,                            
                    size_of_image,
                    pose_style,
                    facerender,
                    exp_weight,
                    blink_every,
                    fps):
    voice = 'zh-CN-XiaoxiaoNeural' if voice not in tts.SUPPORTED_VOICE else voice
    s = time.time()
    llm_response(text, voice, rate, volume, pitch)
    e = time.time()
    print("Using Time", e-s)
    pose_style = random.randint(0, 45)
    s = time.time()
    driven_audio = 'answer.wav'
    video = sad_talker.test2(source_image,
                        driven_audio,
                        preprocess_type,
                        is_still_mode,
                        enhancer,
                        batch_size,                            
                        size_of_image,
                        pose_style,
                        facerender,
                        exp_weight,
                        use_ref_video,
                        ref_video,
                        ref_info,
                        use_idle_mode,
                        length_of_audio,
                        blink_every,
                        fps)
    e = time.time()
    print("Using Time", e-s)
    # print(video)
    return video, 'answer.vtt'

def main():
    
    with gr.Blocks(analytics_enabled=False, title = 'Linly-Talker') as inference:
        gr.HTML(description)
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):
                with gr.Tabs(elem_id="sadtalker_source_image"):
                        with gr.TabItem('Source image'):
                            with gr.Row():
                                source_image = gr.Image(label="Source image", source="upload", type="filepath", elem_id="img2img_image").style(width=512)
                
                
                with gr.Tabs(elem_id="question_audio"):
                    with gr.TabItem('对话'):
                        with gr.Column(variant='panel'):
                            question_audio = gr.Audio(source="microphone",type="filepath", info = '语音对话')
                            input_text = gr.Textbox(label="Input Text", lines=3, info = '文字对话')
                            with gr.Accordion("Advanced Settings",
                                        open=False,
                                        visible=True) as parameter_article:
                                voice = gr.Dropdown(tts.SUPPORTED_VOICE, values='zh-CN-XiaoxiaoNeural', label="Voice")
                                rate = gr.Slider(minimum=-100,
                                                    maximum=100,
                                                    value=0,
                                                    step=1.0,
                                                    label='Rate')
                                volume = gr.Slider(minimum=0,
                                                        maximum=100,
                                                        value=100,
                                                        step=1,
                                                        label='Volume')
                                pitch = gr.Slider(minimum=-100,
                                                    maximum=100,
                                                    value=0,
                                                    step=1,
                                                    label='Pitch')

                            asr_text = gr.Button('语音识别（语音对话后点击）')
                            asr_text.click(fn=asr,inputs=[question_audio],outputs=[input_text])
                
                # with gr.Tabs(elem_id="response_audio"):
                #     with gr.TabItem("语音选择"):
                #         with gr.Column(variant='panel'):
                #             voice = gr.Dropdown(VOICES, values='zh-CN-XiaoxiaoNeural')
                            
                            
                with gr.Tabs(elem_id="text_examples"): 
                    gr.Markdown("## Text Examples")
                    examples =  [
                        ['应对压力最有效的方法是什么？'],
                        ['如何进行时间管理？'],
                        ['为什么有些人选择使用纸质地图或寻求方向，而不是依赖GPS设备或智能手机应用程序？'],
                        ['近日，苹果公司起诉高通公司，状告其未按照相关合约进行合作，高通方面尚未回应。这句话中“其”指的是谁？'],
                        ['三年级同学种树80颗，四、五年级种的棵树比三年级种的2倍多14棵，三个年级共种树多少棵?'],
                        ['撰写一篇交响乐音乐会评论，讨论乐团的表演和观众的整体体验。'],
                        ['翻译成中文：Luck is a dividend of sweat. The more you sweat, the luckier you get.'],
                    ]
                    gr.Examples(
                        examples = examples,
                        inputs = [input_text],
                    )
                    
            # driven_audio = 'answer.wav'           
            with gr.Column(variant='panel'): 
                with gr.Tabs(elem_id="sadtalker_checkbox"):
                    with gr.TabItem('Settings'):
                        with gr.Accordion("Advanced Settings",
                                        open=False) as parameter_article:
                            gr.Markdown("SadTalker: need help? please visit our [[best practice page](https://github.com/OpenTalker/SadTalker/blob/main/docs/best_practice.md)] for more detials")
                            with gr.Column(variant='panel'):
                                # width = gr.Slider(minimum=64, elem_id="img2img_width", maximum=2048, step=8, label="Manually Crop Width", value=512) # img2img_width
                                # height = gr.Slider(minimum=64, elem_id="img2img_height", maximum=2048, step=8, label="Manually Crop Height", value=512) # img2img_width
                                with gr.Row():
                                    pose_style = gr.Slider(minimum=0, maximum=45, step=1, label="Pose style", value=0) #
                                    exp_weight = gr.Slider(minimum=0, maximum=3, step=0.1, label="expression scale", value=1) # 
                                    blink_every = gr.Checkbox(label="use eye blink", value=True)

                                with gr.Row():
                                    size_of_image = gr.Radio([256, 512], value=256, label='face model resolution', info="use 256/512 model? 256 is faster") # 
                                    preprocess_type = gr.Radio(['crop', 'resize','full', 'extcrop', 'extfull'], value='crop', label='preprocess', info="How to handle input image?")
                                
                                with gr.Row():
                                    is_still_mode = gr.Checkbox(label="Still Mode (fewer head motion, works with preprocess `full`)")
                                    facerender = gr.Radio(['facevid2vid', 'PIRender'], value='facevid2vid', label='facerender', info="which face render?")
                                    
                                with gr.Row():
                                    batch_size = gr.Slider(label="batch size in generation", step=1, maximum=10, value=1)
                                    fps = gr.Slider(label='fps in generation', step=1, maximum=30, value =25)
                                    enhancer = gr.Checkbox(label="GFPGAN as Face enhancer(slow)")                                               

                
                            
                with gr.Tabs(elem_id="sadtalker_genearted"):
                    gen_video = gr.Video(label="Generated video", format="mp4",scale=0.8)
                    
                submit = gr.Button('Generate', elem_id="sadtalker_generate", variant='primary')
            submit.click(
                fn=text_response,
                inputs=[input_text,
                        voice, rate, volume, pitch,
                        source_image, 
                        preprocess_type,
                        is_still_mode,
                        enhancer,
                        batch_size,                            
                        size_of_image,
                        pose_style,
                        facerender,
                        exp_weight,
                        blink_every,
                        fps], 
                outputs=[gen_video]
                )


    
        with gr.Row():
            examples = [
                [
                    'examples/source_image/full_body_2.png',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/full_body_1.png',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/full_body_1.png',
                    'crop',
                    False,
                    False
                ],
    
                [
                    'examples/source_image/full3.png',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/full4.jpeg',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/full4.jpeg',
                    'crop',
                    False,
                    False
                ],
                
                [
                    'examples/source_image/art_13.png',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/art_5.png',
                    'crop',
                    False,
                    False
                ],
                [
                    'examples/source_image/art_5.png',
                    'crop',
                    False,
                    False
                ],
            ]
            gr.Examples(examples=examples,
                        fn=text_response,
                        inputs=[
                            source_image,
                            preprocess_type,
                            is_still_mode,
                            enhancer], 
                        outputs=[gen_video],
                        # cache_examples=True,
                        )
    return inference


    
if __name__ == "__main__":
    # funasr = FunASR()
    # local 
    # llm = Linly(mode='offline',model_path="./Chinese-LLaMA-2-7B-hf/")
    # api

    # llm = Gemini(model_path='gemini-pro', api_key=None, proxy_url=None) # 需要自己加入google的apikey
    # llm = Qwen(mode='offline',model_path="Qwen/Qwen-1_8B-Chat")
    # 自动下载
    # llm = Linly(mode='offline',model_path="Linly-AI/Chinese-LLaMA-2-7B-hf")
    # 手动下载指定路径
    llm = Linly(mode=mode, model_path=model_path)
    sad_talker = SadTalker(lazy_load=True)
    openaiasr = OpenAIASR('base')
    tts = EdgeTTS()
    gr.close_all()
    demo = main()
    demo.queue()
    # demo.launch()
    demo.launch(server_name="0.0.0.0",
                server_port=port,
                ssl_certfile=ssl_certfile,
                ssl_keyfile=ssl_keyfile,
                ssl_verify=False,
                debug=True)
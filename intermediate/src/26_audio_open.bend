import Base

# This must be run with an audio device; CI checks syntax/types only.
def main() -> IO(Unit):
  do IO<Unit>:
    audio: Audio <- IO.try(Audio, Audio.open(44100))
    written: Audio & U32 <- Audio.write(audio, Nil{})
    (out, frames) = written
    Audio.close(out)

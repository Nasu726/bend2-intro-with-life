import Base

# This must be run with an audio device; CI checks syntax/types only.
def finish(pair: Audio & U32) -> IO(Unit):
  (audio, written) = pair
  Audio.close(audio)

def main() -> IO(Unit):
  do IO<Unit>:
    audio: Audio <- IO.try(Audio, Audio.open(44100))
    written: Audio & U32 <- Audio.write(audio, Nil{})
    finish(written)

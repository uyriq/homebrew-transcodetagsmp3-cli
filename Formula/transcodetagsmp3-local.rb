class Transcodetagsmp3Local < Formula
  desc "Local dev formula for transcodetagsmp3"
  homepage "https://github.com/uyriq/homebrew-transcodetagsmp3-cli"
  url "file:///tmp/transcodetagsmp3-local.tar.gz"
  sha256 "63c2a959ba070cc23a599a45f0c06ebc6f298123c46c5715f9c797448142de9a"
  license "MIT"
  version "0.2.1-local"

  depends_on "python@3.12"

  on_macos do
    depends_on :macos => :monterey
  end

  resource "mutagen" do
    url "https://files.pythonhosted.org/packages/source/m/mutagen/mutagen-1.47.0.tar.gz"
    sha256 "719fadef0a978c31b4cf3c956261b3c58b6948b32023078a2117b1de09f0fc99"
  end

  def install
    app = libexec/"app"
    app.install "fix_mp3_tags.py"
    app.install "transcodetagsmp3_cli.py"
    (app/"linux").mkpath
    (app/"linux/nautilus").install "linux/nautilus/transcodetagsmp3_extension.py.tmpl"

    py = Formula["python@3.12"].opt_bin/"python3.12"

    vendor = libexec/"vendor"
    vendor.mkpath
    resource("mutagen").stage do
      system py, "-m", "pip", "install", "--no-deps", "--target", vendor, "."
    end

    (bin/"transcodetagsmp3").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{app}:#{vendor}"
      exec "#{py}" "#{app}/transcodetagsmp3_cli.py" "$@"
    EOS
  end

  def post_install
    return unless OS.mac?

    unless quiet_system bin/"transcodetagsmp3", "install-macos-service", "--user", "--force"
      opoo "Finder Quick Action was not auto-installed. Run: transcodetagsmp3 install-macos-service --user --force"
    end
  end

  test do
    assert_match "usage:", shell_output("#{bin}/transcodetagsmp3 --help")
  end
end

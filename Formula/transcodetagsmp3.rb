class Transcodetagsmp3 < Formula
  desc "Fix garbled MP3 ID3 tags from CP1251/Latin-1 to UTF-8"
  homepage "https://github.com/uyriq/homebrew-transcodetagsmp3-cli"
  url "https://github.com/uyriq/homebrew-transcodetagsmp3-cli/releases/download/v0.1.0/transcodetagsmp3-v0.1.0.tar.gz"
  sha256 "3eaf19a14b7524fabbbeaee7e8440939b6ef90b07e050c95ea346710a5a650b7"
  license "MIT"

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

    # Install mutagen into a private vendor path from a pinned Homebrew resource.
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

    system bin/"transcodetagsmp3", "install-macos-service", "--user", "--force"
  end

  test do
    assert_match "usage:", shell_output("#{bin}/transcodetagsmp3 --help")
  end
end

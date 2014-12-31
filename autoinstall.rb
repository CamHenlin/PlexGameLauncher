#!/System/Library/Frameworks/Ruby.framework/Versions/Current/usr/bin/ruby
# This is a hack on the homebrew installer
HOMEBREW_REPO = 'https://github.com/CamHenlin/PlexGameLauncher/raw/master'
DROPBOX_LINK = 'http://dl.dropbox.com/u/9111377'

module Tty extend self
  def blue; bold 34; end
  def white; bold 39; end
  def red; underline 31; end
  def reset; escape 0; end
  def bold n; escape "1;#{n}" end
  def underline n; escape "4;#{n}" end
  def escape n; "\033[#{n}m" if STDOUT.tty? end
end

class Array
  def shell_s
    cp = dup
    first = cp.shift
    cp.map{ |arg| arg.gsub " ", "\\ " }.unshift(first) * " "
  end
end

def ohai *args
  puts "#{Tty.blue}==>#{Tty.white} #{args.shell_s}#{Tty.reset}"
end

def warn warning
  puts "#{Tty.red}Warning#{Tty.reset}: #{warning.chomp}"
end

def system *args
  abort "Failed during: #{args.shell_s}" unless Kernel.system(*args)
end

def sudo *args
  ohai "/usr/bin/sudo", *args
  system "/usr/bin/sudo", *args
end

def getc  # NOTE only tested on OS X
  system "/bin/stty raw -echo"
  if STDIN.respond_to?(:getbyte)
    STDIN.getbyte
  else
    STDIN.getc
  end
ensure
  system "/bin/stty -raw echo"
end

def wait_for_user
  puts
  puts "Plex Game Launcher Installer. Press RETURN to continue or any other key to abort."
  c = getc
  # we test for \r and \n because some stuff does \r instead
  abort unless c == 13 or c == 10
end

module Version
  def <=>(other)
    split(".").map { |i| i.to_i } <=> other.split(".").map { |i| i.to_i }
  end
end

def macos_version
  @macos_version ||= `/usr/bin/sw_vers -productVersion`.chomp[/10\.\d+/].extend(Version)
end

# Invalidate sudo timestamp before exiting
at_exit { Kernel.system "/usr/bin/sudo", "-k" }

wait_for_user if STDIN.tty?

ohai "Downloading and installing PlexGameLauncher..."
# -m to stop tar erroring out if it can't modify the mtime for root owned directories
# pipefail to cause the exit status from curl to propogate if it fails
# we use -k for curl because Leopard has a bunch of bad SSL certificates
curl_flags = "OL"
curl_flags << "k" if macos_version <= "10.5"
system "/bin/bash -o pipefail -c '/bin/mkdir tempplexgamelauncher'"
Dir.chdir "tempplexgamelauncher"
ohai "Downloading emulators..."
system "/bin/bash -o pipefail -c '/usr/bin/curl -#{curl_flags} #{DROPBOX_LINK}/Emulators%20v1.5.3.zip'"
ohai "Unpacking emulators..."
system "/bin/bash -o pipefail -c '/usr/bin/unzip Emulators%20v1.5.3.zip'"
ohai "Downloading gamelauncher..."
system "/bin/bash -o pipefail -c '/usr/bin/curl -#{curl_flags} #{HOMEBREW_REPO}/gamelauncher.zip'"
ohai "Unpacking gamelauncher..."
system "/bin/bash -o pipefail -c '/usr/bin/unzip gamelauncher.zip'"
ohai "Ready to install..."
system "/bin/bash -o pipefail -c 'sudo ./install.sh'"
# r.chdir "tempplexgamelauncher"
# r.chdir "gamelauncher"
# stem "/bin/bash -o pipefail -c 'sudo ls'"
Dir.chdir ".."
# Dir.chdir ".."
system "/bin/bash -o pipefail -c '/bin/rm -rf ./tempplexgamelauncher'"

ohai "Installation successful!"

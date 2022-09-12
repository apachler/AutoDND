# Maintainer: Andreas Pachler <apachler@paan-systems.com>
pkgname=AutoDND-git
pkgver=r3.3a3a579
pkgrel=1
pkgdesc="Add schedule to the Gnome Do Not Disturb function."
arch=('any')
url="https://github.com/apachler/AutoDND"
license=('GPL3')
groups=()
depends=('python')
makedepends=('git')
provides=("${pkgname%-git}")
conflicts=("${pkgname%-git}")
replaces=()
backup=()
options=()
install=
source=("${pkgname%-git}::git+https://github.com/apachler/AutoDND.git")
noextract=()
md5sums=('SKIP')

pkgver() {
	cd "$srcdir/${pkgname%-git}"
	printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
	cd "$srcdir/${pkgname%-git}"
        install -Dm755 "autodnd" "/usr/bin/autodnd"
        install -Dm644 "autodnd.png" "/usr/share/icons/hicolor/192x192/autodnd.png"
        install -Dm644 "autodnd.desktop" "/usr/share/applications/autodnd.desktop"
        install -Dm644 "config-sample.txt" "/usr/share/${pkgname%-git}/config-sample.txt"
}

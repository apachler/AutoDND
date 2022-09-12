# Maintainer: Andreas Pachler <apachler@paan-systems.com>
pkgname=autodnd-git
pkgver=r5.638cf2d
pkgrel=1
pkgdesc="Add schedule to the Gnome Do Not Disturb function."
arch=('any')
url="https://github.com/apachler/AutoDND"
license=('GPL3')
groups=()
depends=('python' 'hicolor-icon-theme')
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
        install -Dm755 "files/autodnd" "$pkgdir/usr/bin/autodnd"
        install -Dm644 "files/autodnd.png" "$pkgdir/usr/share/icons/hicolor/192x192/autodnd.png"
        install -Dm644 "files/autodnd.desktop" "$pkgdir/usr/share/applications/autodnd.desktop"
        install -Dm644 "files/config-sample.txt" "$pkgdir/usr/share/${pkgname%-git}/config-sample.txt"
}

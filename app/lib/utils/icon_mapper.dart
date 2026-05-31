import 'package:flutter/material.dart';
import 'package:material_design_icons_flutter/material_design_icons_flutter.dart';

// Maps Font Awesome icon names to Material Design Icons
// This allows easy replacement of font_awesome_flutter with material_design_icons_flutter
class IconMapper {
  static const Map<String, IconData> faToMdiMap = {
    // Navigation & UI
    'house': Icons.home,
    'solidHouse': Icons.home,
    'comments': Icons.chat,
    'solidComments': Icons.forum,
    'listCheck': Icons.checklist,
    'puzzlePiece': Icons.extension,
    'chevronLeft': Icons.chevron_left,
    'chevronRight': Icons.chevron_right,
    'arrowLeft': Icons.arrow_back,
    'arrowUpFromBracket': Icons.share,
    'ellipsis': Icons.more_horiz,
    'ellipsisVertical': Icons.more_vert,

    // Media & Files
    'solidFileLines': Icons.description,
    'camera': Icons.camera_alt,
    'image': Icons.image,
    'solidStar': Icons.star,
    'star': Icons.star_border,

    // Action & Status
    'microphone': Icons.mic,
    'microphoneSlash': Icons.mic_off,
    'play': Icons.play_arrow,
    'pause': Icons.pause,
    'stop': Icons.stop_circle,
    'check': Icons.check,
    'circleCheck': Icons.check_circle,
    'solidCircleCheck': Icons.check_circle,
    'xmark': Icons.close,
    'triangleExclamation': Icons.warning,
    'circleExclamation': Icons.error,
    'circleInfo': Icons.info,
    'circleQuestion': Icons.help_outline,
    'solidCircleQuestion': Icons.help_outline,

    // Device & Connection
    'wifi': Icons.wifi,
    'bluetooth': Icons.bluetooth,
    'signal': Icons.signal_cellular_alt,
    'batteryFull': Icons.battery_full,
    'batteryThreeQuarters': Icons.battery_6_bar,
    'batteryHalf': Icons.battery_50,
    'batteryQuarter': Icons.battery_2_bar,
    'batteryEmpty': Icons.battery_0_bar,
    'chargingStation': Icons.ev_station,
    'sdCard': Icons.storage,
    'microchip': Icons.memory,
    'plug': Icons.power,
    'mobileScreen': Icons.phone_android,
    'mobile': Icons.phone_android,
    'desktop': Icons.desktop_mac,

    // Cloud & Sync
    'cloud': Icons.cloud,
    'solidCloud': Icons.cloud,
    'cloudArrowDown': Icons.cloud_download,
    'circleCheck': Icons.check_circle,
    'clockRotateLeft': Icons.history,

    // Content & Documents
    'book': Icons.menu_book,
    'pen': Icons.edit,
    'copy': Icons.content_copy,
    'clone': Icons.content_copy,
    'clipboard': Icons.assignment,
    'share': Icons.share,
    'solidShareFromSquare': Icons.share,
    'download': Icons.download,
    'upload': Icons.upload,

    // Settings & Control
    'gear': Icons.settings,
    'lock': Icons.lock,
    'linkSlash': Icons.link_off,
    'ban': Icons.cancel,
    'key': Icons.key,
    'rotateLeft': Icons.rotate_left,
    'arrowRotateLeft': Icons.rotate_left,
    'arrowsRotate': Icons.sync,
    'trashCan': Icons.delete,
    'filter': Icons.filter_list,
    'search': Icons.search,
    'magnifyingGlass': Icons.search,

    // Organization
    'solidFolder': Icons.folder,
    'folder': Icons.folder_open,
    'briefcase': Icons.work,
    'label': Icons.label,

    // People & Social
    'solidUser': Icons.person,
    'user': Icons.person_outline,
    'userGroup': Icons.group,
    'users': Icons.people,
    'solidHeart': Icons.favorite,
    'heart': Icons.favorite_border,
    'userAstronaut': Icons.public,

    // Status & Info
    'solidBell': Icons.notifications,
    'bell': Icons.notifications_none,
    'solidMessage': Icons.mail,
    'solidComment': Icons.comment,
    'commentDots': Icons.comment,
    'solidLightbulb': Icons.lightbulb,
    'lightbulb': Icons.lightbulb_outline,

    // Brand icons (basic Material replacements)
    'google': Icons.g_mobiledata,
    'apple': Icons.apple,
    'appStoreIos': Icons.apple,
    'googlePlay': Icons.android,

    // AI & Tech
    'robot': Icons.smart_toy,
    'brain': Icons.psychology,
    'code': Icons.code,
    'codeBranch': Icons.branch,
    'server': Icons.dns,
    'industry': Icons.factory,
    'fingerprint': Icons.fingerprint,
    'hashtag': Icons.tag,
    'barcode': Icons.barcode_reader,
    'networkWired': Icons.router,

    // Activities & Features
    'gamepad': Icons.sports_esports,
    'music': Icons.music_note,
    'palette': Icons.palette,
    'globe': Icons.public,
    'plane': Icons.flight,
    'cartShopping': Icons.shopping_cart,
    'moneyBill': Icons.money,
    'wallet': Icons.wallet_giftcard,
    'solidHospital': Icons.local_hospital,
    'trophy': Icons.emoji_events,
    'gift': Icons.card_giftcard,
    'phone': Icons.phone,

    // Indicators & Symbols
    'waveSquare': Icons.waves,
    'boltLightning': Icons.flash_on,
    'bolt': Icons.flash_on,
    'infinity': Icons.all_inclusive,
    'screwdriverWrench': Icons.construction,
    'burger': Icons.restaurant,
    'calendarDay': Icons.calendar_today,
    'calendarDays': Icons.calendar_month,
    'solidCalendar': Icons.calendar_today,
    'crown': Icons.crown,
    'wandMagicSparkles': Icons.auto_awesome,
    'chartSimple': Icons.bar_chart,
    'chartLine': Icons.trending_up,
    'gaugeHigh': Icons.dashboard,
    'plus': Icons.add,
    'eye': Icons.visibility,
    'eyeSlash': Icons.visibility_off,
    'arrowRightArrowLeft': Icons.compare_arrows,
    'cubes': Icons.apps,
    'clock': Icons.schedule,
    'shieldHalved': Icons.shield,
    'solidEnvelope': Icons.mail,
    'walkieTalkie': Icons.walkie_talkie,
  };

  /// Get Material Design icon from Font Awesome icon name
  static IconData getMaterialIcon(String faIconName) {
    return faToMdiMap[faIconName] ?? Icons.help_outline;
  }
}

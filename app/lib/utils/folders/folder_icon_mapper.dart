import 'package:flutter/material.dart';

/// Maps folder icon strings (emojis) to Material Design IconData.
/// Falls back to a folder icon for unknown values.
IconData folderIconToFa(String? iconString) {
  return _emojiToFaMap[iconString] ?? Icons.folder;
}

/// Mapping from emoji strings to Material Design icons.
const Map<String, IconData> _emojiToFaMap = {
  '📁': Icons.folder,
  '💼': Icons.work,
  '🏠': Icons.home,
  '📚': Icons.menu_book,
  '👨‍👩‍👧‍👦': Icons.people,
  '👤': Icons.favorite,
  '👥': Icons.people,
  '❤️': Icons.favorite,
  '🎮': Icons.sports_esports,
  '✈️': Icons.flight,
  '🏥': Icons.local_hospital,
  '🛒': Icons.shopping_cart,
  '💰': Icons.money,
  '🎵': Icons.music_note,
  '🎨': Icons.palette,
  '📝': Icons.edit,
  '💬': Icons.forum,
  '🌎': Icons.public,
  '🛠️': Icons.construction,
  '🍔': Icons.restaurant,
  '🏆': Icons.emoji_events,
  '🔒': Icons.lock,
  '⭐': Icons.star,
  '🕐': Icons.schedule,
  '📊': Icons.bar_chart,
};

/// List of all available folder icon strings (for use in icon picker UI).
const List<String> folderIconStrings = [
  '📁',
  '💼',
  '🏠',
  '📚',
  '👨‍👩‍👧‍👦',
  '❤️',
  '🎮',
  '✈️',
  '🏥',
  '🛒',
  '💰',
  '🎵',
  '🎨',
  '📝',
  '💬',
  '🌎',
  '🛠️',
  '🍔',
  '🏆',
  '🔒',
];

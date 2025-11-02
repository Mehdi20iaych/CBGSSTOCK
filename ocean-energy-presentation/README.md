# Ocean Energy Production Presentation

A beautiful, modern, and interactive presentation about ocean energy production built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 🌊 **12 Comprehensive Slides** covering all aspects of ocean energy
- 🎨 **Beautiful Gradients** with ocean-themed color palettes
- ⌨️ **Keyboard Navigation** - Use arrow keys to navigate
- 🖱️ **Click Navigation** - Navigation buttons and slide indicators
- 📱 **Fully Responsive** - Works on all screen sizes
- ✨ **Smooth Animations** - Fade-in effects and transitions
- 🎯 **Progress Tracking** - Visual slide indicators and counter

## Presentation Content

1. **Title Slide** - Introduction to Ocean Energy
2. **What is Ocean Energy?** - Overview and potential
3. **Types of Ocean Energy** - Four main technologies
4. **Tidal Energy** - Predictable and powerful
5. **Wave Energy** - Capturing ocean motion
6. **Ocean Thermal Energy** - Temperature difference power
7. **Benefits** - Why invest in ocean power
8. **Current Projects** - Leading projects worldwide
9. **Environmental Considerations** - Balancing power and nature
10. **Challenges** - Obstacles to overcome
11. **Future Outlook** - A wave of opportunity
12. **Closing Slide** - Thank you

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Installation

```bash
# Install dependencies
npm install

# Run development server (if needed for editing)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Viewing the Presentation

1. After running `npm run dev` or `npm start`, open your browser
2. Navigate to `http://localhost:3000`
3. Use the following controls:
   - **Arrow Keys** (← →) - Navigate between slides
   - **Navigation Buttons** - Click left/right arrows
   - **Slide Indicators** - Click dots to jump to specific slides

## Technology Stack

- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **React Hooks** - State management with useState

## Design Features

- Clean, modern aesthetic with appropriate whitespace
- Ocean-themed gradient backgrounds for each slide
- Typography-focused design without external icon dependencies
- Smooth transitions and fade-in animations
- Accessible design with ARIA labels
- Responsive layouts for mobile, tablet, and desktop

## Project Structure

```
ocean-energy-presentation/
├── app/
│   ├── page.tsx          # Main presentation component
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles and animations
├── public/               # Static assets
├── package.json          # Dependencies
└── README.md            # This file
```

## Customization

To customize the presentation:

1. **Edit Slides**: Modify the `slides` array in `app/page.tsx`
2. **Change Colors**: Update gradient classes (e.g., `from-blue-600 via-cyan-500 to-teal-400`)
3. **Add Content**: Add new slide objects with title, subtitle, and points/sections
4. **Styling**: Adjust Tailwind classes or add custom CSS in `globals.css`

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

This project is open source and available for educational purposes.

---

Built with ❤️ using Next.js and Tailwind CSS

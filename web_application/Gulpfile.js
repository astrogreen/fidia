/*!
 * gulp
 * $ npm install gulp-autoprefixer gulp-cssnano gulp-imagemin gulp-rename
 */

// Load plugins

var gulp = require('gulp'),
    autoprefixer = require('gulp-autoprefixer'),
    cssnano = require('gulp-cssnano'),
    imagemin = require('gulp-imagemin'),
    rename = require("gulp-rename");

// Images
// gulp.task('images', function() {
//   return gulp.src('restapi_app/static/restapi_app/img/**/*')
//     .pipe(imagemin({ optimizationLevel: 3, progressive: true, interlaced: true }))
//     .pipe(gulp.dest('dist/assets/img'))
//     .pipe(notify({ message: 'Images task complete' }));
// });

// Styles
gulp.task('styles', function() {
  return gulp.src('restapi_app/static/restapi_app/less/main.css')
    .pipe(autoprefixer('last 2 version'))
    .pipe(rename({suffix: '.min'}))
    .pipe(cssnano())
    .pipe(gulp.dest('restapi_app/static/restapi_app/css'))
    // .pipe(notify({ message: 'Styles task complete' }));
});


// Default task
gulp.task('default', function(){
    gulp.start('styles');
});

// Watch
gulp.task('watch', function(){
   gulp.watch('restapi_app/static/restapi_app/less/**/*.css', ['styles']);
});